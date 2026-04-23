import json
from pathlib import Path
from fastapi import FastAPI

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "wired_articles.json"

@app.get("/")
def root():
    return {"message": "Wired Articles API is running"}

@app.get("/articles")
def get_articles():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data