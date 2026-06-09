from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from src.etl import load_stock_data


stock_list = [
    'QNC', 'AAPL', 'TSLA', 'GOOGL', 'IREN',
    'NVDA', 'MU', 'PL', 'QBTS', 'RGTI'
]


def fetch_symbol(symbol):
    load_stock_data(symbol)


with DAG(
    dag_id="stock_ingestion_multi",
    start_date=datetime(2026, 1, 1),
    schedule="*/30 * * * *",
    catchup=False
) as dag:

    for symbol in stock_list:

        PythonOperator(
            task_id=f"ingest_{symbol}",
            python_callable=fetch_symbol,
            op_kwargs={"symbol": symbol}
        )