
import mysql.connector
from config import Config

def reset_database():
    try:
        db = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = db.cursor()

        with open('schema.sql', 'r') as f:
            sql_script = f.read()

        statements = sql_script.split(';')

        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as err:
                    print(f"Error executing statement: {err}\nStatement: {statement}")

        db.commit()
        print("Database reset successfully.")
        db.close()

    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    reset_database()
