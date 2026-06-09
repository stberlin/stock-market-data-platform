from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from src.etl.load_stock_data import main_stock
from src.etl.alert_engine import main_alert



with DAG(
    dag_id="stock_pipeline_ingest_then_alert",
    start_date=datetime(2026, 1, 1),
    schedule="*/30 * * * *",
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