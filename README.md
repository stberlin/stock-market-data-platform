# Stock Market Data Platform 📈

A data engineering pipeline for automated stock market data collection, storage, analysis, and notification.

The project fetches financial market data from external APIs, processes the data through an automated ETL pipeline, stores it in a PostgreSQL database, and generates analysis-based notifications.

## Architecture Overview

```
Twelve Data API
        |
        ↓
Python Data Ingestion Pipeline
        |
        ↓
PostgreSQL Database
        |
        ↓
Apache Airflow Scheduler
        |
        ↓
Data Analysis & Processing
        |
        ↓
Telegram Notifications
```

## Features

* Automated retrieval of stock market data via REST API
* ETL pipeline for extracting, transforming, and loading financial data
* Containerized environment using Docker
* PostgreSQL database for structured data storage
* Workflow orchestration with Apache Airflow
* Automated stock analysis
* Telegram notifications based on analysis results

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

```
stock-market-data-platform/

├── dags/
│   ├── stock_pipeline.py
│   ├── stock_pipeline_dag_alerts.py
│   ├── stock_pipeline_ingestion_only.py
│   └── stock_pipeline_v1.py
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
│   │   └── init_db.py
│   │
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── load_stock_data.py
│   │   ├── alert_engine.py
│   │   ├── alert_engine_v1.py
│   │   └── test.py
│   │
│   └── config.py
│
├── .gitignore
├── README.md
├── docker-compose.yml
└── requirements.txt
```

### Directory Description

| Directory / File | Description |
|---|---|
| `dags/` | Apache Airflow DAG definitions for scheduling and orchestrating stock data pipelines |
| `stock_pipeline.py` | Main production pipeline combining data ingestion, processing, and storage |
| `stock_pipeline_ingestion_only.py` | DAG responsible for retrieving and loading stock market data |
| `stock_pipeline_dag_alerts.py` | DAG including automated alert generation |
| `stock_pipeline_v1.py` | Previous pipeline version used for development and testing |
| `src/api/` | API integration layer |
| `stock_api.py` | Client for retrieving stock market data from external APIs |
| `src/database/` | Database management and connection handling |
| `connection.py` | PostgreSQL database connection configuration |
| `init_db.py` | Database initialization and setup |
| `src/etl/` | Data processing and business logic |
| `load_stock_data.py` | Loads processed stock data into the database |
| `alert_engine.py` | Generates alerts based on stock market conditions |
| `alert_engine_v1.py` | Previous version of the alert logic |
| `test.py` | Testing scripts |
| `config.py` | Central application configuration |
| `docker-compose.yml` | Container configuration for running the application stack |
| `requirements.txt` | Python dependencies |

## Data Pipeline

### 1. Data Extraction

Stock market data is retrieved from the Twelve Data API.

The pipeline collects relevant market information and prepares the raw API responses for further processing.

### 2. Data Storage

Processed data is stored in PostgreSQL.

The database provides a structured storage layer for historical market information and enables efficient querying for analysis.

### 3. Workflow Automation

Apache Airflow manages the execution schedule of the pipeline.

The workflow automatically triggers data extraction, transformation, storage, and analysis tasks.

### 4. Data Analysis

The stored market data is analyzed using Python.

Examples:

* price development analysis
* performance calculations
* indicator calculations
* identification of relevant market movements

### 5. Notifications

Analysis results are automatically delivered through Telegram notifications.

This allows users to receive relevant insights without manually querying the database.

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

* Add a dashboard using Streamlit
* Implement additional market indicators
* Add machine learning based predictions
* Improve data quality monitoring
* Add automated testing
* Deploy the platform to cloud infrastructure

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


