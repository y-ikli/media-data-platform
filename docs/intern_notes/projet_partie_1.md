# Étape 1 : environnement local reproductible

## Objectif
Mettre en place un environnement **local** reproductible pour :
- exécuter Airflow (UI + scheduler),
- monter le dossier `dags/`,
- préparer l’exécution future des pipelines (sans données réelles pour l’instant).

**Résultat attendu** : un DAG minimal tourne et apparaît en **Success** dans l’UI Airflow.

---

## 0.0 — Pré-requis
- Docker + Docker Compose installés
- Port 8080 libre (Airflow UI)
- Repo déjà initialisé (dossiers + fichiers)

---

## 0.1 — Arborescence minimum à avoir

```bash
mkdir -p dags logs plugins
mkdir -p src
```

---

## 0.2 — Créer `docker-compose.yaml` (Airflow local)

Copie-colle ce fichier à la racine du repo : `docker-compose.yaml`

```yaml
version: "3.8"

x-airflow-common: &airflow-common
  image: apache/airflow:2.9.3
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "false"
    AIRFLOW__CORE__LOAD_EXAMPLES: "false"
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG: "true"
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - ./src:/opt/airflow/src
  depends_on:
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U airflow"]
      interval: 5s
      timeout: 5s
      retries: 10

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command: -c "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com"
    restart: "no"

  airflow-webserver:
    <<: *airflow-common
    command: airflow webserver
    ports:
      - "8080:8080"

  airflow-scheduler:
    <<: *airflow-common
    command: airflow scheduler
```

---

## 0.3 — Créer un DAG minimal (smoke test)

Créer `dags/hello_airflow.py`

```python
from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def say_hello() -> None:
    print("hello airflow")


with DAG(
    dag_id="hello_airflow",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["smoke_test"],
) as dag:
    task_hello = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello,
    )

    task_hello
```

---

## 0.4 — Démarrer Airflow

```bash
docker compose up airflow-init
docker compose up -d
```

---

## 0.5 — Vérifications (success criteria)

### Vérif 1 — Services up
```bash
docker compose ps
```

Tu dois voir :
- `airflow-webserver` running
- `airflow-scheduler` running
- `postgres` healthy 

pour vérifier healthy de postgres :
```bash
docker inspect -f '{{.State.Health.Status}}' media-data-platform-postgres-1
```
### Vérif 2 — UI Airflow
- Ouvre : http://localhost:8080
- Login : `admin`
- Password : `admin`

### Vérif 3 — DAG visible et exécutable
- Le DAG `hello_airflow` apparaît
- Clique “Trigger DAG”
- Le run passe en **Success**

---

## 0.6 — Dépannage rapide (si blocage)

### Webserver ne démarre pas / DB error
```bash
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

### Voir les logs
```bash
docker compose logs -f airflow-webserver
```

```bash
docker compose logs -f airflow-scheduler
```

---

## 0.7 — Indicateur de réussite (DoD)
```text
- Airflow UI accessible sur localhost:8080
- DAG hello_airflow visible
- Un run manuel finit Success
- Repo contient docker-compose.yaml + dags/hello_airflow.py
```

---

