
import mysql.connector
from config import Config

def inspect():
    try:
        db = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = db.cursor()

        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        for table in tables:
            print(f"\n--- Columns in '{table}' ---")
            cursor.execute(f"DESCRIBE {table}")
            for col in cursor.fetchall():
                print(col)

        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
