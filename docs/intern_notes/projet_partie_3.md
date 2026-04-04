# Partie 3 — Ingestion Source #1 → Raw historisé (API mock)

## Objectif
Implémenter **le premier pipeline d’ingestion réel** :
- une seule source,
- données **mock** (API simulée),
- écriture en **raw historisé**,
- ingestion **incrémentale et idempotente**.

Cette étape valide le **pattern d’ingestion** qui sera répliqué pour toutes les autres sources.

---

## 3.1 — Source choisie (MVP)

```text
Source : google_ads
Type   : API (mock)
Grain  : campaign × date
Format : JSON
```

---

## 3.2 — Principe d’ingestion

### Flux logique

```text
API mock (Python)
   ↓
Extraction par date
   ↓
Ajout métadonnées techniques
   ↓
Écriture Raw (BigQuery ou fichiers locaux)
```

### Règles clés
- **Incrémental** : ingestion par fenêtre de dates.
- **Idempotent** : relancer un run ne crée pas de doublons.
- **Historisé** : aucune suppression / mise à jour destructive.

---

## 3.3 — Schéma raw cible

### Table cible
```text
mdp_raw.raw_google_ads__campaign_daily
```

### Colonnes métier (payload)
```text
date            DATE
account_id      STRING
campaign_id     STRING
campaign_name   STRING
impressions     INT64
clicks          INT64
spend           NUMERIC
conversions     INT64
```

### Colonnes techniques (obligatoires)
```text
ingested_at     TIMESTAMP
extract_run_id  STRING
source          STRING
```

---

## 3.4 — Arborescence à créer

```bash
mkdir -p src/ingestion/google_ads
mkdir -p data/samples
```

---

## 3.5 — Données mock (API simulée)

Créer `data/samples/google_ads_campaign_daily.json`

```json
[
  {
    "date": "2024-01-01",
    "account_id": "acc_001",
    "campaign_id": "camp_001",
    "campaign_name": "Brand Search",
    "impressions": 1000,
    "clicks": 50,
    "spend": 120.50,
    "conversions": 8
  },
  {
    "date": "2024-01-02",
    "account_id": "acc_001",
    "campaign_id": "camp_001",
    "campaign_name": "Brand Search",
    "impressions": 1100,
    "clicks": 55,
    "spend": 130.00,
    "conversions": 9
  }
]
```

---

## 3.6 — Script d’extraction (mock API)

Créer `src/ingestion/google_ads/extract.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import list, dict


DATA_PATH = Path("data/samples/google_ads_campaign_daily.json")


def extract_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    with DATA_PATH.open() as f:
        data = json.load(f)

    return [
        row
        for row in data
        if start_date <= row["date"] <= end_date
    ]
```

---

## 3.7 — Script de chargement raw

Créer `src/ingestion/google_ads/load_raw.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import list, dict
import uuid


def enrich_with_metadata(rows: list[dict], source: str) -> list[dict]:
    run_id = str(uuid.uuid4())
    ingested_at = datetime.now(tz=timezone.utc).isoformat()

    enriched = []
    for row in rows:
        enriched.append(
            {
                **row,
                "ingested_at": ingested_at,
                "extract_run_id": run_id,
                "source": source,
            }
        )
    return enriched
```

---

## 3.8 — Script d’ingestion end-to-end

Créer `src/ingestion/google_ads/run_ingestion.py`

```python
from __future__ import annotations

from extract import extract_campaign_daily
from load_raw import enrich_with_metadata


def run(start_date: str, end_date: str) -> list[dict]:
    rows = extract_campaign_daily(start_date, end_date)
    enriched_rows = enrich_with_metadata(rows, source="google_ads")
    return enriched_rows


if __name__ == "__main__":
    data = run(start_date="2024-01-01", end_date="2024-01-02")
    for row in data:
        print(row)
```

---

## 3.9 — Intégration Airflow (DAG ingestion simple)

Créer `dags/google_ads_ingestion.py`

```python
from __future__ import annotations

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.ingestion.google_ads.run_ingestion import run


with DAG(
    dag_id="google_ads_ingestion_raw",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ingestion", "raw"],
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_google_ads_raw",
        python_callable=run,
        op_kwargs={
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
        },
    )

    ingest_task
```

---

## 3.10 — Indicateurs de réussite (DoD)

```text
- Le DAG google_ads_ingestion_raw apparaît dans Airflow
- Un run manuel passe en SUCCESS
- Les données enrichies contiennent ingested_at, extract_run_id, source
- Relancer le DAG ne génère pas d’erreur
```

---

## Ce que cette étape valide
- Pattern d’ingestion reproductible
- Séparation extraction / enrichissement
- Base prête pour multi-sources
- Airflow utilisé comme orchestrateur réel

---
> En production :

# Au lieu de lire un JSON, on appellerait l'API Google Ads
from google.ads.googleads.client import GoogleAdsClient
client = GoogleAdsClient.load_from_storage()
response = client.service.search(query=f"SELECT campaign.id, metrics.impressions WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'")

> Ajout dynamique au PYTHONPATH :

_SRC_DIR = (Path(__file__).resolve().parents[1] / "src").as_posix()
sys.path.insert(0, _SRC_DIR)

> Idempotence complète nécessiterait :

En BigQuery : utiliser MERGE ou INSERT ... ON CONFLICT DO UPDATE
Clé primaire : (date, campaign_id, platform) pour éviter les doublons
Garder trace du dernier extract_run_id pour chaque ligne

┌─────────────────────────────────────────────────────────────┐
│                    PARTIE 3 & 4 : INGESTION                 │
└─────────────────────────────────────────────────────────────┘

Source 1: Google Ads API (mock: JSON)
   ↓ extract.py (filtre par date)
   ↓ load_raw.py (+ metadata)
   ↓ run_ingestion.py
   → [2 lignes enrichies]
   
Source 2: Meta Ads API (mock: JSON)
   ↓ extract.py (filtre par date)
   ↓ load_raw.py (+ metadata)
   ↓ run_ingestion.py
   → [4 lignes enrichies]

┌─────────────────────────────────────────────────────────────┐
│              Metadata standardisée (3 champs)               │
├─────────────────────────────────────────────────────────────┤
│ ingested_at      → "2026-01-20T12:21:14+00:00" (timestamp)  │
│ extract_run_id   → "a14dd98a-..." (UUID unique)             │
│ source           → "google_ads" ou "meta_ads"               │
└─────────────────────────────────────────────────────────────┘

         DAG Airflow (orchestration)
              ↓
         Trigger manuel
              ↓
         Logs tracés
              ↓
    Success ✅ (données prêtes pour BigQuery)