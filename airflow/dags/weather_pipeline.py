"""Hourly weather pipeline: ingest (Python) -> transform + test (dbt build in its own container).

Hourly, not every few minutes: Weatherstack's free tier allows ~100 calls/month per key,
and the source itself only refreshes observations a few times per hour.
"""

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

sys.path.append("/opt/airflow/ingestion")

HOST_PROJECT_DIR = os.environ["HOST_PROJECT_DIR"]  # absolute path of this repo on the host
DBT_ENV = {
    k: os.environ[k]
    for k in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
}


def ingest() -> int:
    from weather_ingestion import run

    return run()


with DAG(
    dag_id="weather_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["weather", "dbt"],
) as dag:
    ingest_task = PythonOperator(task_id="ingest_weather", python_callable=ingest)

    dbt_build = DockerOperator(
        task_id="dbt_build",
        image="ghcr.io/dbt-labs/dbt-postgres:1.9.latest",
        command="build --profiles-dir /usr/app",
        working_dir="/usr/app",
        environment=DBT_ENV,
        mounts=[Mount(source=f"{HOST_PROJECT_DIR}/dbt", target="/usr/app", type="bind")],
        network_mode=os.getenv("DOCKER_NETWORK", "weather-data-pipeline_weather-net"),
        docker_url="unix://var/run/docker.sock",
        auto_remove="success",
    )

    ingest_task >> dbt_build
