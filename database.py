import os
import time

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection(retries=5, delay=2):
    """Attempts to connect to the DB with retries."""
    attempt = 0
    while attempt < retries:
        try:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
        except Exception:
            attempt += 1
            print(f"Database not ready... (Attempt {attempt}/{retries})")
            time.sleep(delay)

    print("Could not connect to the database. Exiting.")
    return None
