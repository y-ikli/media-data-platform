"""Configuration lue dans les variables d'environnement.

Aucune valeur propre à un projet n'est écrite dans le code : tout vient de l'environnement
(fichier ``.env`` en local, variables du job en production).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

DEFAULT_LOCATION = "europe-west1"
DEFAULT_RAW_DATASET = "ads_raw"


class ConfigError(RuntimeError):
    """Une variable de configuration obligatoire manque."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Paramètres nécessaires pour écrire dans BigQuery."""

    project_id: str
    location: str = DEFAULT_LOCATION
    raw_dataset: str = DEFAULT_RAW_DATASET

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        """Construit les paramètres depuis ``environ`` (par défaut, les variables du processus).

        Une variable vide est traitée comme absente.
        """
        env = os.environ if environ is None else environ

        def read(name: str) -> str | None:
            value = env.get(name, "").strip()
            return value or None

        project_id = read("GCP_PROJECT_ID")
        if project_id is None:
            raise ConfigError("GCP_PROJECT_ID n'est pas défini (voir .env.example)")
        return cls(
            project_id=project_id,
            location=read("BQ_LOCATION") or DEFAULT_LOCATION,
            raw_dataset=read("BQ_RAW_DATASET") or DEFAULT_RAW_DATASET,
        )
