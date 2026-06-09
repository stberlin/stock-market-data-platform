from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from src.etl import alert_engine


with DAG(
    dag_id="stock_price_drop_alerts",
    start_date=datetime(2026, 1, 1),
    schedule="*/30 * * * *",
    catchup=False,
    tags=["stocks", "alerts"]
) as dag:

    run_script = PythonOperator(
        task_id="run_price_drop_script",
        python_callable=alert_engine
    )