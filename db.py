from dotenv import load_dotenv
load_dotenv()

import os

USE_SQLITE = os.getenv("USE_SQLITE") == "1"   # set this when running locally

if USE_SQLITE:
    import sqlite3

    def get_connection():
        # local dev DB file
        conn = sqlite3.connect("dev.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
else:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    def get_connection():
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432"),
            sslmode=os.getenv("DB_SSLMODE", "require"),  # set DB_SSLMODE=disable for localhost PG
            cursor_factory=RealDictCursor,
        )
