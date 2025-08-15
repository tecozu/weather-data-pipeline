from airflow import DAG
import sys
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount 
from datetime import datetime, timedelta

sys.path.append('/opt/airflow/api_request')

def safe_main_callable():
    from insert_records import main
    return main()

default_args ={
    'description': 'A DAG to orchestrate data',
    'start_date': datetime(2025,8,3),
    'catchup':False,
}

dag = DAG(
    dag_id='weather-api-dbt-orchestrator',
    default_args=default_args,
    schedule= timedelta(minutes=5)
)

with dag:
    task1 = PythonOperator(
        task_id = 'ingest_data_task',
        python_callable = safe_main_callable 
    )

    # DBT Docker Operator to run transformations in dbt container defined in docker-compose.yaml
    task2 = DockerOperator(
        task_id = 'transform_data_task',
        image = 'ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
        command = 'run',
        working_dir = '/usr/app',
        mounts = [
            Mount(source = '/root/repos/weather-data-project/dbt/my_project',
                target = '/usr/app',
                type = 'bind'),
            Mount(source = '/root/repos/weather-data-project/dbt/profiles.yml',
                target = '/root/.dbt/profiles.yml',
                type = 'bind'),            
        ],
        network_mode = 'weather-data-project_my-network',
        docker_url = 'unix://var/run/docker.sock',
        auto_remove = 'success'
    )

    task1 >> task2  # Set task dependencies