CREATE TABLE IF NOT EXISTS wired_db (
    id SERIAL PRIMARY KEY,
    title TEXT,
    url TEXT UNIQUE,
    description TEXT,
    author TEXT,
    scraped_at TIMESTAMP
);
