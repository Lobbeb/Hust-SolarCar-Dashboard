# backend/cleanup.py
import pymysql

from backend.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# How old data to keep (in days):
RETENTION_DAYS = 30

# Make sure these match your real table names
TABLES = [
    "`Battery Data Table`",
    "`Motor Data Table`",
    "`MPPT Data Table`",
    "`Vehicle Data Table`",
]

def connect_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )

def cleanup_old_rows():
    """
    Delete rows older than RETENTION_DAYS from each telemetry table.
    """
    sql = "DELETE FROM {table} WHERE timestamp < NOW() - INTERVAL %s DAY"
    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(sql.format(table=table), (RETENTION_DAYS,))
        conn.commit()
        print(f"[cleanup] Removed telemetry older than {RETENTION_DAYS} days.")
    except Exception as e:
        print("[cleanup] ERROR during cleanup:", e)
    finally:
        if conn:
            conn.close()
