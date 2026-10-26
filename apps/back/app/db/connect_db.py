import psycopg
from dotenv import load_dotenv

from apps.back.app.configuration import PG_CONNECTION_STRING, TABLE_NAMES

def connect_to_postgres():
    try:
        conn = psycopg.connect(PG_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None
    