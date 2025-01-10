import psycopg2
from psycopg2.extras import DictCursor

def test_connection():
    try:
        conn = psycopg2.connect(
            dbname="reverie_memory",
            user="reverie_user",
            password="dreamNoLonger00",
            host="localhost"
        )
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
