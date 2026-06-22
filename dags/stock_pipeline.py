from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from src.etl.load_stock_data import main_stock
from src.etl.alert_engine_v1 import main_alert
import pendulum

ny_tz = pendulum.timezone("America/New_York")

with DAG(
    dag_id="stock_pipeline_ingest_then_alert",
    start_date=pendulum.datetime(2026, 1, 1, tz=ny_tz),
    schedule="*/30 9-16 * * 1-5",
    catchup=False,
    tags=["stocks", "pipeline"]
) as dag:

    # 1. INGESTION TASK
    ingest_task = PythonOperator(
        task_id="stock_ingestion",
        python_callable=main_stock
    )

    # 2. ALERT TASK
    alert_task = PythonOperator(
        task_id="price_drop_alerts",
        python_callable=main_alert
    )

    # 👉 HIER passiert die Reihenfolge
    ingest_task >> alert_task