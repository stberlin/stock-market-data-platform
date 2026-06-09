from airflow.decorators import dag, task
from datetime import datetime

from src.ingestion import load_stock_data
from src.price_drop import check_price_drop

stock_list = [
    "AAPL", "TSLA", "NVDA", "GOOGL", "MU",
    "PL", "QBTS", "RGTI", "IREN", "QNC"
]


@dag(
    dag_id="stock_pipeline_parallel_ingest",
    start_date=datetime(2026, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["stocks", "pipeline"]
)
def pipeline():

    # -------------------------
    # 1. PARALLEL INGESTION
    # -------------------------
    @task
    def ingest(symbol: str):
        load_stock_data(symbol)

    ingested = ingest.expand(symbol=stock_list)

    # -------------------------
    # 2. ALERT (runs AFTER ALL ingest tasks succeed)
    # -------------------------
    @task
    def alerts():
        check_price_drop()

    ingested >> alerts()


dag = pipeline()