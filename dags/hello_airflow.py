""" A simple hello world DAG for Airflow."""
from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def say_hello() -> None:
    """A simple hello world function."""
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