import os
import mysql.connector

def get_connection():
    try:
        return mysql.connector.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"]
        )
    except KeyError as e:
        raise ValueError(f"❌ Environment variable {e} is missing.")
    except mysql.connector.Error as err:
        raise ConnectionError(f"❌ Failed to connect to the database: {err}")
