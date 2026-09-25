"""Connecteur Google Ads.

Seul le mode ``simulated`` est disponible : l'extraction réelle (GAQL) n'est pas implémentée. Demander
le mode ``real`` échoue explicitement plutôt que de charger zéro ligne en silence.
"""

from __future__ import annotations

from mdp.fake_apis.google_ads_api import get_campaign_daily
from mdp.ingestion.base import DataSourceConnector
from mdp.ingestion.schemas import GOOGLE_ADS


class GoogleAdsConnector(DataSourceConnector):
    source_name = "google_ads"
    spec = GOOGLE_ADS

    def __init__(self, data_mode: str = "simulated"):
        if data_mode == "real":
            raise NotImplementedError("Google Ads : extraction réelle (GAQL) non implémentée, utiliser --mode simulated")
        super().__init__(data_mode)

    def extract(self, start_date: str, end_date: str) -> list[dict]:
        return get_campaign_daily(start_date, end_date)
