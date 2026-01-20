
import mysql.connector
from config import Config

def alter_table():
    try:
        db = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = db.cursor()

        # Check if column exists first to avoid error
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='timetable' AND COLUMN_NAME='day'", (Config.DB_NAME,))
        if cursor.fetchone():
            print("Column 'day' already exists.")
        else:
            print("Adding column 'day' to 'timetable' table...")
            cursor.execute("ALTER TABLE timetable ADD COLUMN day VARCHAR(15)")
            print("Column 'day' added successfully.")
        
        db.commit() # Important for ALTER TABLE? Usually auto-commit DDl but good practice.
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    alter_table()
