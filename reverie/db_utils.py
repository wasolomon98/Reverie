from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime, timezone
from contextlib import contextmanager

load_dotenv()
PASSWORD = os.getenv("DATABASE_PASSWORD")

connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname="reverie_memory",
    user="reverie_user",
    password=PASSWORD,
    host="localhost",
    port="5432"
)

@contextmanager
def get_db_connection():
    """
    Context manager for safely acquiring and releasing a database connection.
    """
    connection = None
    try:
        connection = connection_pool.getconn()
        yield connection
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if connection:
            connection_pool.putconn(connection)

def execute_query(query, params=None, fetch=False, fetchone=False):
    """
    Executes a query with the given parameters.

    Args:
        query (str): SQL query to execute.
        params (tuple or dict, optional): Query parameters.
        fetch (bool): Whether to fetch all rows (default: False).
        fetchone (bool): Whether to fetch a single row (default: False).

    Returns:
        list or dict: Fetched rows if fetch or fetchone is True; otherwise None.
    """
    result = None
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if fetchone:
                result = cursor.fetchone()
            elif fetch:
                result = cursor.fetchall()
            connection.commit()
    return result

def close_connection_pool():
    try:
        connection_pool.closeall()
    except Exception as e:
        print(f"Error closing connection pool: {e}")
        raise
