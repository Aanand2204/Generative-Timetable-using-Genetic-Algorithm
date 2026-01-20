
import mysql.connector
from config import Config

def dump_schema():
    try:
        db = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = db.cursor()
        
        with open("schema_dump.txt", "w") as f:
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]

            for table in tables:
                f.write(f"\n--- TABLE: {table} ---\n")
                cursor.execute(f"SHOW CREATE TABLE {table}")
                create_stmt = cursor.fetchone()[1]
                f.write(create_stmt + ";\n")
        
        print("Schema dumped to schema_dump.txt")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_schema()
