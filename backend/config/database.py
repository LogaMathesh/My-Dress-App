import os
import psycopg2

# Database configuration (env vars first, fallback to defaults)
DB_NAME = os.environ.get("DB_NAME", "loga")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "loga")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    print("✅ Database connected successfully")

except Exception as e:
    print("❌ Database connection failed:", e)
    conn = None
    cur = None
