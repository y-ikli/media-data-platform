"""Chargement idempotent dans BigQuery : remplacement atomique d'une fenêtre de dates.

1. Le lot est chargé dans une table temporaire (un seul job de chargement, gratuit), qui expire
   d'elle-même au bout d'une heure si le programme s'arrête avant de la supprimer.
2. Une transaction supprime les lignes de la fenêtre dans la table cible, puis insère le lot.
3. La table temporaire est supprimée.

Rejouer une fenêtre redonne le même état ; une campagne disparue de la source disparaît aussi de
la fenêtre. Le ``DELETE`` filtre la colonne de partition : seuls les jours concernés sont lus.
Une extraction vide ne supprime rien (une panne d'API ne doit pas effacer l'historique).
"""

import logging
from collections.abc import Sequence
from datetime import timedelta

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from adsdata.config import ConfigError, Settings
from adsdata.ingestion.base import utc_now
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import TableSpec
from adsdata.ingestion.validation import Row

logger = logging.getLogger(__name__)

STAGING_TABLE_TTL = timedelta(hours=1)

_LEGACY_TYPE_NAMES = {"INTEGER": "INT64", "FLOAT": "FLOAT64", "BOOLEAN": "BOOL"}
"""BigQuery renvoie parfois les anciens noms des types : ils sont ramenés aux noms standard."""


class SchemaMismatchError(RuntimeError):
    """La table BigQuery existante n'a pas le schéma déclaré dans le code."""


def schema_fields(spec: TableSpec) -> list[bigquery.SchemaField]:
    """Schéma BigQuery d'une table raw, déduit de sa déclaration."""
    return [
        bigquery.SchemaField(
            column.name,
            column.bq_type.value,
            mode="REQUIRED" if column.required else "NULLABLE",
        )
        for column in spec.columns
    ]


def _signature(field: bigquery.SchemaField) -> tuple[str, str, str]:
    """Nom, type standard et mode d'une colonne, pour comparer deux schémas."""
    field_type = str(field.field_type)
    return field.name, _LEGACY_TYPE_NAMES.get(field_type, field_type), str(field.mode)


def replace_window_script(spec: TableSpec, target: str, staging: str) -> str:
    """Script SQL du remplacement de fenêtre, avec les dates en paramètres ``@start``, ``@end``."""
    columns = ", ".join(f"`{name}`" for name in spec.column_names)
    partition = f"`{spec.partition_field}`"
    return (
        "BEGIN TRANSACTION;\n"
        f"DELETE FROM `{target}` WHERE {partition} BETWEEN @start AND @end;\n"
        f"INSERT INTO `{target}` ({columns}) SELECT {columns} FROM `{staging}`;\n"
        "COMMIT TRANSACTION;"
    )


class BigQueryLoader:
    """Écrit les lots validés dans la zone raw de BigQuery."""

    def __init__(self, settings: Settings, client: bigquery.Client | None = None) -> None:
        """Le client BigQuery est créé à la première utilisation, sauf s'il est fourni."""
        self.settings = settings
        self._client = client

    @property
    def client(self) -> bigquery.Client:
        """Client BigQuery du projet configuré."""
        if self._client is None:
            self._client = bigquery.Client(
                project=self.settings.project_id, location=self.settings.location
            )
        return self._client

    @property
    def dataset_id(self) -> str:
        """Identifiant complet du dataset raw."""
        return f"{self.settings.project_id}.{self.settings.raw_dataset}"

    def table_id(self, spec: TableSpec) -> str:
        """Identifiant complet de la table raw de ``spec``."""
        return f"{self.dataset_id}.{spec.name}"

    def ensure_table(self, spec: TableSpec) -> None:
        """Crée la table si elle manque ; vérifie son schéma si elle existe.

        Le dataset, lui, n'est jamais créé ici : il appartient à Terraform.
        """
        try:
            self.client.get_dataset(self.dataset_id)
        except NotFound as exc:
            raise ConfigError(
                f"dataset {self.dataset_id} introuvable : il est créé par Terraform (infra/)"
            ) from exc

        expected = schema_fields(spec)
        try:
            table = self.client.get_table(self.table_id(spec))
        except NotFound:
            table = bigquery.Table(self.table_id(spec), schema=expected)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field=spec.partition_field
            )
            table.clustering_fields = list(spec.cluster_by)
            table.labels = {"gere_par": "adsdata"}
            self.client.create_table(table)
            logger.info("table %s créée", self.table_id(spec))
            return

        actual = [_signature(field) for field in table.schema]
        wanted = [_signature(field) for field in expected]
        if actual != wanted:
            raise SchemaMismatchError(
                f"{self.table_id(spec)} : schéma différent de la déclaration\n"
                f"  attendu : {wanted}\n  trouvé  : {actual}"
            )

    def replace_window(
        self, spec: TableSpec, rows: Sequence[Row], window: DateWindow, run_id: str
    ) -> int:
        """Remplace atomiquement les lignes de ``window`` par ``rows`` ; renvoie leur nombre."""
        if not rows:
            logger.warning("aucune ligne pour %s (%s) : fenêtre conservée", spec.name, window)
            return 0

        self.ensure_table(spec)
        target = self.table_id(spec)
        staging_id = f"{target}__load_{run_id.replace('-', '')}"
        staging = bigquery.Table(staging_id, schema=schema_fields(spec))
        staging.expires = utc_now() + STAGING_TABLE_TTL
        self.client.create_table(staging)
        try:
            self.client.load_table_from_json(
                [dict(row) for row in rows],
                staging_id,
                job_config=bigquery.LoadJobConfig(
                    schema=schema_fields(spec),
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                ),
            ).result()
            self.client.query(
                replace_window_script(spec, target, staging_id),
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("start", "DATE", window.start),
                        bigquery.ScalarQueryParameter("end", "DATE", window.end),
                    ]
                ),
            ).result()
        finally:
            self.client.delete_table(staging_id, not_found_ok=True)

        logger.info("%d lignes chargées dans %s (%s)", len(rows), target, window)
        return len(rows)
