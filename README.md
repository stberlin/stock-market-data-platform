# Stock Market Data Platform 📈

A data engineering pipeline for automated stock market data collection, storage, analysis, and notification.

The project fetches financial market data from external APIs, processes the data through an automated ETL pipeline, stores it in a PostgreSQL database, and generates analysis-based notifications.

## Architecture Overview

```
                Twelve Data API
                       │
                       ▼
                stock_api.py
                       │
                       ▼
          transform_stock_data()
                       │
                       ▼
          repository.py (SQLAlchemy)
                       │
                       ▼
      PostgreSQL (ON CONFLICT DO NOTHING)
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
      Alert Engine          Airflow DAGs
             │
             ▼
      Telegram Notifications
```

## Features

- Automated ETL pipeline for historical stock market data
- Modular architecture (API, ETL, Repository, Database)
- PostgreSQL storage with idempotent inserts using `ON CONFLICT DO NOTHING`
- SQLAlchemy repository layer
- Apache Airflow workflow orchestration
- Configurable stock watchlist
- Automatic retry handling for API rate limits
- Timezone conversion (New York ↔ Berlin)
- Telegram alert engine
- Structured logging
- Unit and integration tests using pytest
- Docker-based development environment

## Technology Stack

### Programming & Data Processing

* Python
* Pandas
* REST APIs
* SQL

### Database

* PostgreSQL

### Infrastructure & Automation

* Docker
* Docker Compose
* Apache Airflow

### External Services

* Twelve Data API
* Telegram Bot API

## Project Structure

```text
stock-market-data-platform/

├── dags/
│   ├── stock_pipeline.py
│   ├── stock_pipeline_dag_alerts.py
│   ├── stock_pipeline_ingestion_only.py
│   └── stock_pipeline_v1.py
│
├── scripts/
│   ├── debug_alerts.py
│   ├── debug_api.py
│   └── debug_db.py
│
├── src/
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── stock_api.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── init_db.py
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── alert_engine.py
│   │   ├── alert_engine_v1.py
│   │   └── load_stock_data.py
│   │
│   ├── logging_config.py
│   └── config.py
│
├── tests/
│   ├── test_repository.py
│   └── test_transform_stock_data.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── pytest.ini
├── README.md
├── docker-compose.yml
└── requirements.txt
```

### Directory Description

| Directory / File | Description |
|---|---|
| `dags/` | Apache Airflow DAG definitions for scheduling and orchestrating ETL workflows |
| `stock_pipeline.py` | Main production pipeline for data ingestion, transformation, and storage |
| `stock_pipeline_ingestion_only.py` | Development DAG for testing the data ingestion process |
| `stock_pipeline_dag_alerts.py` | Development DAG for testing the alert generation workflow |
| `stock_pipeline_v1.py` | Legacy pipeline version retained for reference during development |
| `scripts/` | Standalone debugging and development scripts |
| `debug_api.py` | Debug script for testing API connectivity and responses |
| `debug_db.py` | Debug script for testing database connectivity and queries |
| `debug_alerts.py` | Debug script for testing the alert engine |
| `src/api/` | API integration layer |
| `stock_api.py` | Retrieves stock market data from the Twelve Data API with retry and rate-limit handling |
| `src/database/` | Database models, connection management, and persistence layer |
| `connection.py` | SQLAlchemy database engine configuration |
| `init_db.py` | Initializes the database schema |
| `models.py` | SQLAlchemy table definitions and database schema |
| `repository.py` | Repository layer responsible for database operations and idempotent inserts |
| `src/etl/` | ETL processing and business logic |
| `load_stock_data.py` | Extracts, transforms, and loads stock market data into PostgreSQL |
| `alert_engine.py` | Main alert engine for detecting significant market movements |
| `alert_engine_v1.py` | Legacy alert engine implementation retained for reference |
| `logging_config.py` | Central logging configuration used across the application |
| `config.py` | Central application configuration and constants |
| `tests/` | Unit and integration tests |
| `test_transform_stock_data.py` | Unit tests for data transformation and timezone conversion |
| `test_repository.py` | Integration tests for PostgreSQL repository and duplicate handling |
| `.env.example` | Example environment variables configuration |
| `pytest.ini` | Pytest configuration |
| `docker-compose.yml` | Docker Compose configuration for the complete application stack |
| `requirements.txt` | Python project dependencies |

## Data Pipeline

Extract
↓

Transform

↓

Load (Repository Layer)

↓

PostgreSQL

↓

Alert Engine

↓

Telegram

### 5. Notifications

Analysis results are automatically delivered through Telegram notifications.

This allows users to receive relevant insights without manually querying the database.

### 6. Testing

The project includes both unit and integration tests to ensure reliable data processing and database operations.

Run all tests:

```bash
pytest -v
```

Current test coverage includes:

- Data transformation from API responses
- Validation of invalid numeric input
- Timezone conversion (New York ↔ Berlin)
- PostgreSQL duplicate protection using `ON CONFLICT DO NOTHING`

The integration tests verify that duplicate records are handled correctly by the database, ensuring idempotent data ingestion.

### 7. Logging

The project uses Python's built-in `logging` module instead of `print()` statements to provide structured and configurable log output.

Current log levels include:

- `INFO` – General pipeline execution and processing status
- `WARNING` – Recoverable issues such as API rate limits
- `ERROR` – API failures and unexpected processing errors

Structured logging simplifies debugging, integrates seamlessly with Apache Airflow logs, and provides a solid foundation for production monitoring.

## Setup

### Requirements

* Docker
* Docker Compose
* API key from Twelve Data
* Telegram Bot Token

### Installation

Clone the repository:

```bash
git clone https://github.com/stberlin/stock-market-data-platform.git

cd stock-market-data-platform
```

Create an environment file:

```bash
touch .env
```

Add required environment variables:

```
TWELVE_DATA_API_KEY=your_api_key

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

Start the application:

```bash
docker-compose up -d
```

## Example Workflow

1. Airflow triggers the scheduled pipeline
2. Stock data is requested from the API
3. Data is validated and transformed
4. Results are stored in PostgreSQL
5. Analysis scripts evaluate market conditions
6. Telegram notification is generated

## Future Improvements

Possible extensions:

* Implement CI/CD using GitHub Actions
* Add database migrations with Alembic
* Introduce data quality validation and monitoring
* Add application metrics and health checks
* Build an interactive dashboard using Streamlit
* Implement additional technical indicators
* Add cloud deployment (AWS, Azure, or GCP)
* Support multiple financial data providers
* Add real-time data streaming capabilities
* Integrate machine learning based anomaly detection

## Purpose

This project demonstrates practical experience in:

* building automated data pipelines
* working with APIs
* database design
* workflow orchestration
* containerized applications
* data-driven automation

## Disclaimer

This project is for educational and technical demonstration purposes only and does not provide investment advice.


