-- This file is used to initialize the PostgreSQL database for Airflow

CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow_db WITH OWNER airflow;