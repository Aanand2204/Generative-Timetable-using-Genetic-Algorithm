
from src.routes.routes import perform_timetable_generation
from src.database.database import connect_db
import logging
import sys

# Setup logging to console
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def reproduce():
    print("--- Starting Reproduction ---")
    class_name = "MSc FY"
    semester = "2" # Testing string vs int issue
    priorities = {
        "ML & AI": 5, "NLP": 4, "DSA": 3, "DAV": 2, "ELECTIVE (BA)": 1, "MINOR PROJECT": 5
    }
    school_id = 1 # SPPU DOT

    print(f"Calling perform_timetable_generation with: Class={class_name}, Sem={semester}, School={school_id}")
    
    # We need to mock session context if routes.py uses session['time_config']
    # routes.py: time_config = session.get('time_config')
    # Use a mock session or patch it? 
    # Or set it manually if we can import session. 
    # Flask session depends on request context.
    
    # Let's mock session by updating the function or injecting.
    # Actually, easier: Update session in a request context.
    
    from flask import Flask, session
    app = Flask(__name__)
    app.secret_key = 'test'
    
    with app.test_request_context():
        # Setup session
        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM schools WHERE school_id = %s", (school_id,))
        school = cursor.fetchone()
        db.close()
        
        session['time_config'] = {
            'start_time': str(school['start_time']),
            'end_time': str(school['end_time']),
            'lecture_duration': school['lecture_duration'],
            'break_start': str(school['break_start_time']) if school['break_start_time'] else None,
            'break_duration': school['break_duration']
        }
        session['school_id'] = school_id
        
        saved, error = perform_timetable_generation(class_name, semester, priorities, school_id)
        
        print(f"Result Saved Entries: {len(saved) if saved else 0}")
        print(f"Error: {error}")

if __name__ == "__main__":
    reproduce()
