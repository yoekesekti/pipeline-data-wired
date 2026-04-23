from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
from sqlalchemy import create_engine, text

API_URL = "http://host.docker.internal:8000/articles"
DB_URL = "postgresql+psycopg2://postgres:postgres@wired-postgres:5432/wired_db"

def fetch_articles(ti):
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    ti.xcom_push(key="articles_data", value=data)


def transform_articles(ti):
    data = ti.xcom_pull(task_ids="fetch_articles", key="articles_data")
    articles = data[0]["articles"]

    cleaned = []
    for article in articles:
        authors = article.get("author", [])

        if isinstance(authors, list):
            author_value = ", ".join([str(a).strip() for a in authors if str(a).strip()])
        else:
            author_value = str(authors).strip()

        if not author_value:
            author_value = "Unknown"

        cleaned.append({
            "title": (article.get("title") or "").strip(),
            "url": (article.get("url") or "").strip(),
            "description": (article.get("description") or "").strip(),
            "author": author_value,
            "scraped_at": article.get("scraped_at")
        })

    ti.xcom_push(key="cleaned_articles", value=cleaned)


def load_to_postgres(ti):
    articles = ti.xcom_pull(task_ids="transform_articles", key="cleaned_articles")
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        for article in articles:
            conn.execute(text("""
                INSERT INTO wired_db (title, url, description, author, scraped_at)
                VALUES (:title, :url, :description, :author, :scraped_at)
                ON CONFLICT (url) DO NOTHING
            """), article)


with DAG(
    dag_id="wired_pipeline_dag",
    start_date=datetime(2026, 4, 19),
    schedule_interval=None,
    catchup=False,
    tags=["wired", "uts"]
) as dag:

    task_fetch = PythonOperator(
        task_id="fetch_articles",
        python_callable=fetch_articles
    )

    task_transform = PythonOperator(
        task_id="transform_articles",
        python_callable=transform_articles
    )

    task_load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres
    )

    task_fetch >> task_transform >> task_load