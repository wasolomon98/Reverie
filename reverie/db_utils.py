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
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if fetchone:
                return cursor.fetchone()
            elif fetch:
                return cursor.fetchall()
            else:
                connection.commit()

def execute_modify(query, params=None):
    """
    Executes a query for modifying records (INSERT, UPDATE, DELETE).

    Args:
        query (str): SQL query to execute.
        params (tuple or dict, optional): Query parameters.

    Returns:
        None
    """
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()

def close_connection_pool():
    try:
        connection_pool.closeall()
    except Exception as e:
        print(f"Error closing connection pool: {e}")
        raise

def generate_conversation_data():
    return {
        "user_id": "Rewind",  # Current default user
        "interface": None,  # Placeholder; can be set later if needed
        "start_time": datetime.now(timezone.utc),  # Record the current UTC time as the start time
        "end_time": None,  # End time is null at the beginning
        "duration_seconds": None,  # Duration will be calculated when the conversation ends
        "message_count": 0,  # Initialize with 0 messages
        "summary": None,  # No summary initially
        "tags": None,  # Tags will be set later if needed
        "token_usage_user": 0,  # Initialize user token usage as 0
        "token_usage_assistant": 0,  # Initialize assistant token usage as 0
        "token_usage_total": 0,  # Initialize total token usage as 0
        "model_version": None,  # Placeholder; can be set dynamically during the conversation
    }

def generate_message_data(conversation_id: str, role: str, content: str, token_count: int, sentiment_score: float = None, custom_metrics: dict = None):
    return {
        "conversation_id": conversation_id,  # Link to the conversation
        "role": role,  # Role of the sender
        "content": content,  # Message content
        "timestamp": datetime.now(timezone.utc),  # Current UTC time
        "token_count": token_count,  # Number of tokens in the message
        "sentiment_score": sentiment_score,  # Optional sentiment score
        "custom_metrics": custom_metrics,  # Optional additional metrics
    }
