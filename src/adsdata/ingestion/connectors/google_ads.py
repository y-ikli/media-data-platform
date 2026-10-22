"""Connecteur Google Ads.

Seul le mode simulé existe : l'API Google Ads demande un compte annonceur validé par Google.
Le mode réel échoue explicitement, plutôt que de charger zéro ligne ou des données inventées.
"""

from collections.abc import Callable
from datetime import datetime

from adsdata.ingestion.base import Connector, new_run_id, utc_now
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import GOOGLE_ADS, DataMode
from adsdata.simulation import google_ads as simulated_api


class GoogleAdsConnector(Connector):
    """Performances journalières des campagnes Google Ads (simulées)."""

    source_name = "google_ads"
    spec = GOOGLE_ADS

    def __init__(
        self,
        data_mode: DataMode = DataMode.SIMULATED,
        *,
        clock: Callable[[], datetime] = utc_now,
        run_id_factory: Callable[[], str] = new_run_id,
    ) -> None:
        """Refuse le mode réel, non disponible pour Google Ads."""
        if DataMode(data_mode) is DataMode.REAL:
            raise NotImplementedError(
                "Google Ads : extraction réelle non disponible, utiliser le mode simulated"
            )
        super().__init__(data_mode, clock=clock, run_id_factory=run_id_factory)

    def extract(self, window: DateWindow) -> list[dict[str, object]]:
        """Lignes simulées de ``window``."""
        return simulated_api.campaign_daily(window)
