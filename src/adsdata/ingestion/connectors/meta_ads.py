"""Connecteur Meta Ads (Facebook, Instagram) : API Marketing réelle ou données simulées.

En mode réel, l'absence d'identifiants est une erreur : jamais de repli silencieux vers des
données simulées, qui se mélangeraient aux chiffres réels.
"""

import logging
import os
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime
from typing import Protocol

from adsdata.config import ConfigError
from adsdata.ingestion.base import Connector, new_run_id, utc_now
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import META_ADS, DataMode
from adsdata.simulation import meta_ads as simulated_api

logger = logging.getLogger(__name__)

INSIGHT_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "campaign_name",
    "account_currency",
    "impressions",
    "clicks",
    "spend",
    "actions",
    "action_values",
)

DEFAULT_CONVERSION_ACTIONS: tuple[str, ...] = (
    "omni_purchase",
    "purchase",
    "offsite_conversion.fb_pixel_purchase",
)
"""Types d'action comptés comme conversion, par ordre de préférence.

Ils se recouvrent (``omni_purchase`` inclut ``purchase``) : on garde le premier présent au lieu
de les additionner, sinon un même achat serait compté plusieurs fois.
"""

ENGAGEMENT_ACTIONS: Mapping[str, str] = {
    "likes": "post_reaction",
    "comments": "comment",
    "shares": "post",
    "video_views": "video_view",
    "page_engagement": "page_engagement",
}
"""Colonne de la table raw → type d'action Meta."""


class InsightsClient(Protocol):
    """Source des insights Meta (l'API Graph en production, un faux dans les tests)."""

    def fetch(self, window: DateWindow) -> Iterable[Mapping[str, object]]:
        """Insights journaliers par campagne pour ``window``."""
        ...


def _action_values(items: object) -> dict[str, float]:
    """Convertit une liste d'actions Meta (``action_type``, ``value`` en texte) en dictionnaire."""
    if not isinstance(items, list):
        return {}
    values: dict[str, float] = {}
    for item in items:
        if isinstance(item, Mapping) and "action_type" in item and "value" in item:
            values[str(item["action_type"])] = float(str(item["value"]))
    return values


def _first_present(values: Mapping[str, float], wanted: Sequence[str]) -> float | None:
    for action_type in wanted:
        if action_type in values:
            return values[action_type]
    return None


def _count(values: Mapping[str, float], action_type: str) -> int | None:
    value = values.get(action_type)
    return None if value is None else int(value)


def flatten_insight(
    insight: Mapping[str, object],
    conversion_actions: Sequence[str] = DEFAULT_CONVERSION_ACTIONS,
) -> dict[str, object]:
    """Aplatit une ligne d'insights Meta au format de la table raw (fonction pure).

    L'API renvoie les nombres sous forme de texte ; ils sont convertis ici.
    """
    actions = _action_values(insight.get("actions"))
    action_values = _action_values(insight.get("action_values"))
    row: dict[str, object] = {
        "date": str(insight["date_start"]),
        "campaign_id": str(insight["campaign_id"]),
        "campaign_name": insight.get("campaign_name"),
        "impressions": int(str(insight.get("impressions", 0))),
        "clicks": int(str(insight.get("clicks", 0))),
        "conversions": _first_present(actions, conversion_actions),
        "conversion_value": _first_present(action_values, conversion_actions),
        "spend": float(str(insight.get("spend", 0))),
        "account_currency": insight.get("account_currency"),
    }
    for column, action_type in ENGAGEMENT_ACTIONS.items():
        row[column] = _count(actions, action_type)
    return row


class GraphApiInsightsClient:
    """Insights lus avec la bibliothèque officielle ``facebook-business``."""

    def __init__(
        self,
        access_token: str,
        account_id: str,
        app_id: str | None = None,
        app_secret: str | None = None,
    ) -> None:
        """Initialise l'accès à l'API ; l'option ``meta`` doit être installée."""
        try:
            from facebook_business.api import FacebookAdsApi
        except ImportError as exc:
            raise ConfigError(
                "mode real : installer l'option meta (uv sync --extra meta)"
            ) from exc
        FacebookAdsApi.init(app_id=app_id, app_secret=app_secret, access_token=access_token)
        self.account_id = account_id if account_id.startswith("act_") else f"act_{account_id}"

    def fetch(self, window: DateWindow) -> Iterable[Mapping[str, object]]:
        """Insights au niveau campagne, un jour par ligne ; la pagination est gérée par la SDK."""
        from facebook_business.adobjects.adaccount import AdAccount

        insights = AdAccount(self.account_id).get_insights(
            fields=list(INSIGHT_FIELDS),
            params={
                "level": "campaign",
                "time_increment": 1,
                "time_range": {"since": window.start.isoformat(), "until": window.end.isoformat()},
            },
        )
        for insight in insights:
            yield dict(insight)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> GraphApiInsightsClient:
        """Construit le client depuis les variables ``META_ADS_*``."""
        env = os.environ if environ is None else environ
        missing = [k for k in ("META_ADS_ACCESS_TOKEN", "META_ADS_ACCOUNT_ID") if not env.get(k)]
        if missing:
            raise ConfigError(f"mode real : variables manquantes {missing} (voir .env.example)")
        return cls(
            access_token=env["META_ADS_ACCESS_TOKEN"],
            account_id=env["META_ADS_ACCOUNT_ID"],
            app_id=env.get("META_ADS_APP_ID") or None,
            app_secret=env.get("META_ADS_APP_SECRET") or None,
        )


def conversion_actions_from_env(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Lit ``META_CONVERSION_ACTIONS`` (types séparés par des virgules), sinon le défaut."""
    env = os.environ if environ is None else environ
    raw = env.get("META_CONVERSION_ACTIONS", "")
    chosen = tuple(part.strip() for part in raw.split(",") if part.strip())
    return chosen or DEFAULT_CONVERSION_ACTIONS


class MetaAdsConnector(Connector):
    """Performances journalières des campagnes Meta Ads."""

    source_name = "meta_ads"
    spec = META_ADS

    def __init__(
        self,
        data_mode: DataMode = DataMode.SIMULATED,
        *,
        client: InsightsClient | None = None,
        conversion_actions: Sequence[str] | None = None,
        clock: Callable[[], datetime] = utc_now,
        run_id_factory: Callable[[], str] = new_run_id,
    ) -> None:
        """En mode réel, utilise ``client`` ou, à défaut, l'API Graph de l'environnement."""
        super().__init__(data_mode, clock=clock, run_id_factory=run_id_factory)
        self._conversion_actions = tuple(conversion_actions or conversion_actions_from_env())
        self._client: InsightsClient | None = None
        if self.data_mode is DataMode.REAL:
            self._client = client or GraphApiInsightsClient.from_env()

    def extract(self, window: DateWindow) -> list[dict[str, object]]:
        """Lignes de ``window`` : API réelle ou simulation selon le mode."""
        if self._client is None:
            return simulated_api.campaign_daily(window)
        rows = [flatten_insight(i, self._conversion_actions) for i in self._client.fetch(window)]
        logger.info("Meta Ads : %d lignes extraites (%s)", len(rows), window)
        return rows
