
import mysql.connector
from config import Config

def inspect_subjects():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    print("--- Subjects for School 'DOT' (id=3) Class 'FY' ---")
    # First get class_id for 'FY' school_id=3
    cursor.execute("SELECT class_id FROM class WHERE class_name = 'FY' AND school_id = 3")
    cls = cursor.fetchone()
    if not cls:
        print("Class FY not found for school 3")
        return

    class_id = cls['class_id']
    print(f"Class ID: {class_id}")
    
    cursor.execute("SELECT subject_id, subject_name, semester, credits, teacher_id FROM subject WHERE class_id = %s", (class_id,))
    subjects = cursor.fetchall()
    
    if not subjects:
        print("No subjects found for this class.")
        
    for s in subjects:
        print(s)
        print(f"Semester value: {s['semester']} (type: {type(s['semester'])})")

    conn.close()

if __name__ == "__main__":
    inspect_subjects()
