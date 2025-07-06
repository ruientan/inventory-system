# test_db.py

from db import get_connection

try:
    conn = get_connection()
    print("✅ Connected to MySQL successfully!")
    conn.close()
except Exception as e:
    print("❌ Failed to connect:", e)