#!/bin/bash
# Creates the metadata databases for Airflow and Superset with credentials from .env.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${AIRFLOW_DB_USER} WITH PASSWORD '${AIRFLOW_DB_PASSWORD}';
    CREATE DATABASE airflow_db OWNER ${AIRFLOW_DB_USER};
    CREATE USER ${DATABASE_USER} WITH PASSWORD '${DATABASE_PASSWORD}';
    CREATE DATABASE ${DATABASE_DB} OWNER ${DATABASE_USER};
EOSQL
