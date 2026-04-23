import json
from datetime import datetime
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5437/wired_db")

with open("data/wired_articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

articles = data[0]["articles"]

with engine.connect() as conn:
    for article in articles:
        conn.execute(text("""
            INSERT INTO wired_articles (title, url, description, author, scraped_at)
            VALUES (:title, :url, :description, :author, :scraped_at)
            ON CONFLICT (url) DO NOTHING
        """), {
            "title": article["title"],
            "url": article["url"],
            "description": article["description"],
            "author": article["author"],
            "scraped_at": datetime.fromisoformat(article["scraped_at"])
        })
    conn.commit()

print("Data berhasil dimasukkan ke database")