"""Chargement idempotent vers BigQuery : remplacement atomique d'une fenêtre de dates.

Pourquoi pas ``WRITE_APPEND`` : relancer une ingestion dupliquerait les lignes.
Pourquoi pas une charge par partition (``table$AAAAMMJJ``) : une fenêtre de trois ans ferait un job
de chargement par jour, au-delà du quota de 1 500 jobs de chargement par table et par jour.

Principe : un seul job de chargement dans une table temporaire, puis une transaction
``DELETE`` (fenêtre) + ``INSERT`` (lot). Rejouer la même fenêtre donne le même état ; une campagne
disparue de la source disparaît aussi de la fenêtre. Le ``DELETE`` filtre la colonne de partition :
seules les partitions de la fenêtre sont lues.
"""

from __future__ import annotations

import logging
from datetime import date

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from mdp.config import Settings
from mdp.ingestion.schemas import TableSpec

logger = logging.getLogger(__name__)

_BQ_TYPES = {"DATE": "DATE", "STRING": "STRING", "INT64": "INT64", "FLOAT64": "FLOAT64", "TIMESTAMP": "TIMESTAMP"}


def schema_fields(spec: TableSpec) -> list[bigquery.SchemaField]:
    return [
        bigquery.SchemaField(name, _BQ_TYPES[kind], mode="REQUIRED" if required else "NULLABLE")
        for name, kind, required in spec.columns
    ]


def replace_window_statements(table: str, staging: str, start: date, end: date) -> list[str]:
    """Instructions SQL du remplacement de fenêtre (dates ISO validées : pas d'injection possible)."""
    return [
        "BEGIN TRANSACTION",
        f"DELETE FROM `{table}` WHERE date BETWEEN DATE '{start.isoformat()}' AND DATE '{end.isoformat()}'",
        f"INSERT INTO `{table}` SELECT * FROM `{staging}`",
        "COMMIT TRANSACTION",
    ]


class BigQueryLoader:
    def __init__(self, settings: Settings, client: bigquery.Client | None = None):
        self.settings = settings
        self._client = client

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            self._client = bigquery.Client(project=self.settings.project_id, location=self.settings.location)
        return self._client

    def table_id(self, name: str) -> str:
        return f"{self.settings.project_id}.{self.settings.raw_dataset}.{name}"

    def ensure_table(self, spec: TableSpec) -> None:
        """Crée le jeu de données raw s'il manque, puis la table (partitionnée par jour, clusterisée) si elle manque."""
        dataset_id = f"{self.settings.project_id}.{self.settings.raw_dataset}"
        try:
            # Lecture d'abord : en production le compte de service n'a pas le droit de créer des jeux de données
            # (Terraform les crée) ; `create_dataset(exists_ok=True)` exigerait ce droit même s'il existe.
            self.client.get_dataset(dataset_id)
        except NotFound:
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = self.settings.location
            self.client.create_dataset(dataset)
        table = bigquery.Table(self.table_id(spec.name), schema=schema_fields(spec))
        table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY, field="date")
        table.clustering_fields = list(spec.cluster_by)
        self.client.create_table(table, exists_ok=True)

    def replace_window(self, spec: TableSpec, rows: list[dict], start: date, end: date, run_id: str) -> int:
        """Remplace atomiquement les lignes de ``[start, end]`` par ``rows`` ; retourne leur nombre."""
        if not rows:
            logger.warning("Aucune ligne pour %s..%s : rien à remplacer (fenêtre conservée)", start, end)
            return 0

        self.ensure_table(spec)
        target = self.table_id(spec.name)
        staging = f"{target}__load_{run_id.replace('-', '')}"

        job = self.client.load_table_from_json(
            rows,
            staging,
            job_config=bigquery.LoadJobConfig(
                schema=schema_fields(spec),
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
            ),
        )
        try:
            job.result()
            script = ";\n".join(replace_window_statements(target, staging, start, end)) + ";"
            self.client.query(script).result()
        finally:
            self.client.delete_table(staging, not_found_ok=True)

        logger.info("%d lignes chargées dans %s (fenêtre %s..%s)", len(rows), target, start, end)
        return len(rows)
