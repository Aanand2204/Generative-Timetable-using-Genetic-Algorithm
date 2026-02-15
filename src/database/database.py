
import mysql.connector
from src.logic.config import Config
from datetime import timedelta

def connect_db():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
    )

def fetch_data(class_name, semester, school_id):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT class_id FROM class WHERE class_name = %s AND school_id = %s", (class_name, school_id))
    class_id = cursor.fetchone()

    if class_id is None:
        return [], []

    class_id = class_id[0]
    cursor.execute("SELECT subject_name FROM subject WHERE class_id = %s AND semester = %s AND school_id = %s", (class_id, semester, school_id))
    subjects = [row[0] for row in cursor.fetchall()]

    # Timeslots are now generic or per allocation? 
    # For now, sticking to logic where we just need a list? 
    # Actually, timeslots come from school config now usually.
    # But let's keep this query valid just in case.
    cursor.execute("SELECT timeslot FROM timeslot") 
    timeslots = [row[0] for row in cursor.fetchall()]

    db.close()
    return subjects, timeslots

def get_timetable_by_class(class_name, semester, school_id):
    db = connect_db()
    cursor = db.cursor()

    # Get class_id
    cursor.execute("SELECT class_id FROM class WHERE class_name = %s AND school_id = %s", (class_name, school_id))
    result = cursor.fetchone()
    if not result:
        db.close()
        return {}, []
    
    class_id = result[0]

    # Fetch timetable with day and timeslot
    query = """
    SELECT s.subject_name, t.day, ts.timeslot 
    FROM timetable t
    JOIN subject s ON t.subject_id = s.subject_id
    JOIN timeslot ts ON t.time_id = ts.time_id
    WHERE t.class_id = %s AND s.semester = %s AND t.school_id = %s
    """
    cursor.execute(query, (class_id, semester, school_id))
    results = cursor.fetchall()
    
    # Fetch all timeslots for structure
    cursor.execute("SELECT timeslot FROM timeslot")
    all_timeslots = [str(row[0]) for row in cursor.fetchall()]

    db.close()

    timetable = {}
    for subject, day, timeslot in results:
        if isinstance(timeslot, timedelta):
            timeslot = str(timeslot)
        timetable[f"{day}_{timeslot}"] = subject

    return timetable, sorted(all_timeslots)
