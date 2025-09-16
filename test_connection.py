# test_connection.py
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def test_db_connection():
    try:
        # Try to connect
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Test a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ SUCCESS! Connected to your Railway database!")
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED to connect: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()