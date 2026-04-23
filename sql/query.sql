-- query 1
SELECT title, author AS clean_author
FROM wired_db;

-- query 2
SELECT author, COUNT(*) AS total_articles
FROM wired_db
GROUP BY author
ORDER BY total_articles DESC
LIMIT 3;

-- query 3
SELECT *
FROM wired_db
WHERE title ILIKE '%AI%'
   OR description ILIKE '%AI%'
   OR title ILIKE '%Climate%'
   OR description ILIKE '%Climate%'
   OR title ILIKE '%Security%'
   OR description ILIKE '%Security%';