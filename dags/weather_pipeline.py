from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from ingestion.loader import get_cities, get_db_config, load_weather_for_date

def extract_and_load(**context):
    load_weather_for_date(get_cities(), context["ds"], get_db_config())

with DAG(
	dag_id="weather_pipeline",
	description="Extract the logical day, load raw weather, then run dbt.",
	start_date=datetime(2026, 8, 25, tzinfo=timezone.utc),
	schedule="@daily",
	catchup=True,
	max_active_runs=1,
	default_args={
		"retries": 2,
		"retry_delay": timedelta(minutes=2),
	}
) as dag:
	extract_load_task = PythonOperator(
		task_id="extract_and_load",
		python_callable=extract_and_load,
		execution_timeout=timedelta(minutes=10),
	)

	dbt_run = BashOperator(
		task_id="dbt_run",
		bash_command="cd /opt/airflow/dbt/weather_dbt && dbt run",
		execution_timeout=timedelta(minutes=10),
	)

	dbt_test = BashOperator(
		task_id="dbt_test",
		bash_command="cd /opt/airflow/dbt/weather_dbt && dbt test",
		execution_timeout=timedelta(minutes=10),
	)

	extract_load_task >> dbt_run >> dbt_test
