import os
import psycopg2

# DB connection (same as app.py)
conn = psycopg2.connect(
    dbname=os.environ.get("DB_NAME", "loga"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", "loga"),
    host=os.environ.get("DB_HOST", "localhost"),
    port=os.environ.get("DB_PORT", "5432"),
)
cur = conn.cursor()

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploaded_images")

print("Checking files inside:", UPLOAD_FOLDER)

cur.execute("SELECT id, image_path FROM uploads")
rows = cur.fetchall()

deleted = 0

for uid, path in rows:
    filename = os.path.basename(path)
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        print("Deleting broken DB entry:", path)
        cur.execute("DELETE FROM uploads WHERE id = %s", (uid,))
        deleted += 1

conn.commit()
cur.close()
conn.close()

print(f"\n✅ Cleanup complete. Deleted {deleted} broken DB records.")
