"""Registre des connecteurs : ajouter une source = écrire son connecteur et l'enregistrer ici."""

from collections.abc import Mapping
from types import MappingProxyType

from adsdata.ingestion.base import Connector
from adsdata.ingestion.connectors.google_ads import GoogleAdsConnector
from adsdata.ingestion.connectors.meta_ads import MetaAdsConnector

CONNECTORS: Mapping[str, type[Connector]] = MappingProxyType(
    {
        GoogleAdsConnector.source_name: GoogleAdsConnector,
        MetaAdsConnector.source_name: MetaAdsConnector,
    }
)
"""Connecteur de chaque source, par nom de source (lecture seule)."""
