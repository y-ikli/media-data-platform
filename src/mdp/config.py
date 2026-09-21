"""Configuration lue dans l'environnement : aucune valeur de projet n'est codée en dur."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Configuration manquante ou invalide."""


@dataclass(frozen=True)
class Settings:
    project_id: str
    location: str = "europe-west1"
    raw_dataset: str = "mdp_raw"

    @classmethod
    def from_env(cls) -> Settings:
        project = os.getenv("GCP_PROJECT_ID")
        if not project:
            raise ConfigError("GCP_PROJECT_ID n'est pas défini (voir .env.example)")
        return cls(
            project_id=project,
            location=os.getenv("BQ_LOCATION", cls.location),
            raw_dataset=os.getenv("BQ_RAW_DATASET", cls.raw_dataset),
        )
