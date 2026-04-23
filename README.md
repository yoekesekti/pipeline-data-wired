# Wired Data Pipeline Project

Project ini merupakan implementasi pipeline data end-to-end yang mencakup proses scraping, API, orchestration (Airflow), penyimpanan database, hingga reporting menggunakan SQL/Postgree.

---

## Deskripsi Project

Pipeline ini mengambil data artikel dari **Wired.com**, kemudian:

1. Scraping data artikel (judul, URL, deskripsi, author, waktu scrape)
2. Menyimpan hasil scraping dalam format JSON
3. Menyediakan API menggunakan FastAPI (`GET /articles`)
4. Menggunakan Airflow untuk orkestrasi:
   - Fetch data dari API
   - Transform data (cleaning author & format)
   - Load ke database PostgreSQL
5. Menjalankan query untuk reporting

---

## Tools yang Digunakan

- Python
- Selenium (Scraping)
- FastAPI (API)
- Airflow (Orchestration)
- PostgreSQL (Database)
- SQLAlchemy (Database Connection)
- Docker (Containerization)

---

## Struktur Folder
.
├── api/ # FastAPI service
├── dags/ # Airflow DAG
├── scraper/ # Script scraping
├── data/ # Hasil scraping (JSON)
├── sql/ # Query SQL & create table
├── docker-compose.yml # Setup PostgreSQL & Airflow
├── requirements.txt
└── README.md

---

## Cara Menjalankan Project

### 1. Jalankan Database & Airflow (Docker)

```bash
docker compose up -d

```akses airflow
http://localhost:8081

### 2. Jalankan Scraping
python scraper/scrape_wired.py

Output:

data/wired_articles.json

3. Jalankan API
uvicorn api.main:app --reload --port 8000

Endpoint:

http://127.0.0.1:8000/articles

4. Jalankan DAG Airflow
Buka Airflow UI
Aktifkan DAG: wired_pipeline_dag
Klik tombol ▶ (Trigger DAG)

Pipeline:

fetch_articles → transform_articles → load_to_postgres

### Database

Tabel yang digunakan:

wired_articles

Script pembuatan tabel:

sql/create_table.sql
