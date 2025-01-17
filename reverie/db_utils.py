import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import Json
from datetime import datetime, timezone

connection_pool = SimpleConnectionPool(
    minconn = 1,
    maxconn = 10,
    dbname = "reverie_memory",
    user = "reverie_user",
    password = "dreamNoLonger00",
    host = "localhost",
    port = "5432"
)

def get_connection():
    try:
        return connection_pool.getconn()
    except Exception as e:
        print(f"Error retrieving connection: {e}")
        raise

def release_connection(connection):
    try:
        connection_pool.putconn(connection)
    except Exception as e:
        print(f"Error releasing connection: {e}")
        raise

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

def insert_into_table(table_name: str, data: dict):
    """
    Inserts data into a specified PostgreSQL table.

    Parameters:
        table_name (str): The name of the table.
        data (dict): A dictionary of column names and their values.
    """

    # Construct column names and placeholders for SQL
    columns = ", ".join(data.keys())
    placeholders = ", ".join([f"%({key})s" for key in data.keys()])

    # Insertion query
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    try:
        # Connect to the database
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, {k: (Json(v) if isinstance(v, dict) else v) for k, v in data.items()})
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection:
            release_connection(connection)

def update_table_column_by_id(table_name: str, column_name: str, id_column: str, record_id: str, value):
    query = f"UPDATE {table_name} SET {column_name} = %s WHERE {id_column} = %s"
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, (value, record_id))
            connection.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection:
            release_connection(connection)

def get_first_conversation_id():
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id FROM Conversations ORDER BY start_time ASC LIMIT 1;")
            result = cursor.fetchone()
            return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if connection:
            release_connection(connection)

def get_latest_conversation_id():
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id FROM Conversations ORDER BY start_time DESC LIMIT 1;")
            result = cursor.fetchone()
            return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if connection:
            release_connection(connection)

def get_untagged_conversation_ids():
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id FROM Conversations WHERE tags IS NULL ORDER BY start_time ASC;")
            results = cursor.fetchall()
            return [row[0] for row in results]
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if connection:
            release_connection(connection)

def get_recent_messages(num_messages: int = 100):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT role, content FROM messages WHERE role != 'system' ORDER BY timestamp ASC LIMIT %s;", (num_messages,))
            return [{"role": role, "content": content} for role, content in cursor.fetchall()]
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if connection:
            release_connection(connection)

def get_all_messages_in_conversation(conversation_id: str):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = "SELECT message_id, content FROM Messages WHERE conversation_id = %s ORDER BY timestamp ASC;"
            cursor.execute(query, (conversation_id,))
            results = cursor.fetchall()
            return {row[0]: row[1] for row in results}
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return {}
    finally:
        if connection:
            release_connection(connection)

def get_all_untagged_messages_in_conversation(conversation_id: str):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            query = "SELECT message_id, content FROM messages WHERE conversation_id = %s AND (tags is NULL OR tags = '[]') ORDER BY timestamp ASC;"
            cursor.execute(query, (conversation_id,))
            results = cursor.fetchall()
            return {row[0]: row[1] for row in results}
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return {}
    finally:
        if connection:
            release_connection(connection)