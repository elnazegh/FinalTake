
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# Load the private .env file from the backend folder.
# Settings already defined in the terminal take priority.
load_dotenv(Path(__file__).resolve().parent / ".env")


def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    return connection


if __name__ == "__main__":
    connection = get_db_connection()

    if connection.is_connected():
        print("Successfully connected to MySQL!")

    connection.close()
