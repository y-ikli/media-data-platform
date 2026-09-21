"""Connecteur Meta Ads (Facebook / Instagram) : API Marketing réelle ou données simulées.

En mode ``real``, l'absence d'identifiants est une erreur : il n'y a jamais de repli silencieux vers
des données simulées, qui se retrouveraient mélangées à des chiffres réels.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable

from mdp.config import ConfigError
from mdp.fake_apis.meta_ads_api import get_campaign_daily
from mdp.ingestion.base import DataSourceConnector
from mdp.ingestion.schemas import META_ADS

logger = logging.getLogger(__name__)

# Types d'actions Meta comptés comme conversions (configurable : dépend de l'événement pixel de l'annonceur).
DEFAULT_CONVERSION_ACTIONS = ("purchase", "offsite_conversion.fb_pixel_purchase", "omni_purchase")
INSIGHT_FIELDS = ["campaign_id", "campaign_name", "impressions", "clicks", "spend", "actions", "action_values"]


def _sum_actions(items: Iterable[dict] | None, wanted: set[str], cast) -> float | int | None:
    """Somme des ``value`` des actions de types ``wanted`` ; None si aucune n'est présente."""
    values = [cast(a["value"]) for a in items or [] if a.get("action_type") in wanted]
    return sum(values) if values else None


def flatten_insight(row: dict, conversion_actions: Iterable[str] = DEFAULT_CONVERSION_ACTIONS) -> dict:
    """Aplatit une ligne d'insights Meta (fonction pure, testée sans réseau)."""
    wanted = set(conversion_actions)
    actions = {a["action_type"]: int(float(a["value"])) for a in row.get("actions") or []}
    return {
        "date": row["date_start"],
        "campaign_id": str(row["campaign_id"]),
        "campaign_name": row.get("campaign_name"),
        "impressions": int(row.get("impressions", 0)),
        "clicks": int(row.get("clicks", 0)),
        "spend_usd": float(row.get("spend", 0.0)),
        "conversions": _sum_actions(row.get("actions"), wanted, lambda v: int(float(v))),
        "conversion_value": _sum_actions(row.get("action_values"), wanted, float),
        "likes": actions.get("post_reaction"),
        "comments": actions.get("comment"),
        "shares": actions.get("post"),
        "video_views": actions.get("video_view"),
        "page_engagement": actions.get("page_engagement"),
    }


class MetaAdsConnector(DataSourceConnector):
    source_name = "meta_ads"
    spec = META_ADS

    def __init__(self, data_mode: str = "simulated"):
        super().__init__(data_mode)
        self._account_id: str | None = None
        if data_mode == "real":
            self._init_real_api()

    def _init_real_api(self) -> None:
        try:
            from facebook_business.api import FacebookAdsApi
        except ImportError as exc:
            raise ConfigError("Mode real : installer l'extra `meta` (uv sync --extra meta)") from exc
        keys = ("META_ADS_APP_ID", "META_ADS_APP_SECRET", "META_ADS_ACCESS_TOKEN", "META_ADS_ACCOUNT_ID")
        missing = [k for k in keys if not os.getenv(k)]
        if missing:
            raise ConfigError(f"Mode real : variables manquantes {missing}")
        FacebookAdsApi.init(os.environ[keys[0]], os.environ[keys[1]], os.environ[keys[2]])
        self._account_id = os.environ[keys[3]]

    def extract(self, start_date: str, end_date: str) -> list[dict]:
        if self.data_mode == "simulated":
            return get_campaign_daily(start_date, end_date)
        return self._extract_real(start_date, end_date)

    def _extract_real(self, start_date: str, end_date: str) -> list[dict]:
        from facebook_business.adobjects.adaccount import AdAccount

        types = os.getenv("META_CONVERSION_ACTIONS")
        actions = tuple(t.strip() for t in types.split(",")) if types else DEFAULT_CONVERSION_ACTIONS
        insights = AdAccount(self._account_id).get_insights(
            fields=INSIGHT_FIELDS,
            params={"time_range": {"since": start_date, "until": end_date}, "time_increment": 1, "level": "campaign"},
        )
        rows = [flatten_insight(dict(r), actions) for r in insights]
        logger.info("Meta Ads : %d lignes extraites (%s..%s)", len(rows), start_date, end_date)
        return rows
