
import mysql.connector
from config import Config

def inspect_data():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    print("--- Schools ---")
    cursor.execute("SELECT school_id, school_name, username FROM schools")
    schools = cursor.fetchall()
    for s in schools:
        print(s)

    print("\n--- Classes ---")
    cursor.execute("SELECT class_id, class_name, school_id FROM class")
    classes = cursor.fetchall()
    for c in classes:
        print(c)

    print("\n--- Timetable Entries (Limit 5) ---")
    cursor.execute("SELECT t.timetable_id, t.school_id, c.class_name, t.day, ts.timeslot FROM timetable t JOIN class c ON t.class_id = c.class_id JOIN timeslot ts ON t.time_id = ts.time_id LIMIT 5")
    entries = cursor.fetchall()
    for e in entries:
        print(e)
        
    print("\n--- Timetable Count for 'FY' Sem '2' ---")
    # We need to join subject to check semester
    sql = """
    SELECT COUNT(*) as count 
    FROM timetable t
    JOIN class c ON t.class_id = c.class_id
    JOIN subject s ON t.subject_id = s.subject_id
    WHERE c.class_name = 'FY' AND s.semester = 2
    """
    cursor.execute(sql)
    print(cursor.fetchone())

    conn.close()

if __name__ == "__main__":
    inspect_data()
