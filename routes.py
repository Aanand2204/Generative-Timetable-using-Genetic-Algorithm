
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from database import connect_db, fetch_data, get_timetable_by_class
from algorithms import genetic_algorithm
from functools import wraps

main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'school_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/manage_teachers', methods=['GET', 'POST'])
@login_required
def manage_teachers():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            name = request.form.get('teacher_name')
            
            cursor.execute("""
                INSERT INTO teacher (teacher_name, school_id)
                VALUES (%s, %s)
            """, (name, session['school_id']))
            db.commit()
            # flash('Teacher added successfully!', 'success')
        except Exception as e:
            # flash(f'Error: {str(e)}', 'error')
            pass
            
    cursor.execute("SELECT * FROM teacher WHERE school_id = %s", (session['school_id'],))
    teachers = cursor.fetchall()
    db.close()
    return render_template('manage_teachers.html', teachers=teachers)

@main_bp.route('/manage_subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    school_id = session['school_id']

    # Ensure a default course exists (MVP shortcut)
    cursor.execute("SELECT course_id FROM course WHERE school_id = %s LIMIT 1", (school_id,))
    course = cursor.fetchone()
    if not course:
        cursor.execute("INSERT INTO course (course_name, school_id) VALUES ('Standard', %s)", (school_id,))
        db.commit()
        course_id = cursor.lastrowid
    else:
        course_id = course['course_id']

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'add_class':
                class_name = request.form.get('class_name')
                cursor.execute("INSERT INTO class (class_name, school_id) VALUES (%s, %s)", (class_name, school_id))
                db.commit()
            
            elif action == 'add_subject':
                subject_name = request.form.get('subject_name')
                class_id = request.form.get('class_id')
                teacher_id = request.form.get('teacher_id')
                credits = request.form.get('credits') 
                semester = request.form.get('semester')
                
                cursor.execute("""
                    INSERT INTO subject (subject_name, class_id, course_id, teacher_id, semester, credits, school_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (subject_name, class_id, course_id, teacher_id, semester, credits, school_id))
                db.commit()
                
        except Exception as e:
            pass

    # Fetch Data
    cursor.execute("SELECT * FROM class WHERE school_id = %s", (school_id,))
    classes = cursor.fetchall()

    cursor.execute("SELECT * FROM teacher WHERE school_id = %s", (school_id,))
    teachers = cursor.fetchall()
    
    # Fetch subjects with joins
    cursor.execute("""
        SELECT s.*, c.class_name, t.teacher_name 
        FROM subject s
        JOIN class c ON s.class_id = c.class_id
        JOIN teacher t ON s.teacher_id = t.teacher_id
        WHERE s.school_id = %s
    """, (school_id,))
    subjects = cursor.fetchall()

    db.close()
    return render_template('manage_subjects.html', classes=classes, teachers=teachers, subjects=subjects)

@main_bp.route('/credits')
@login_required
def credits_page():
    return render_template('credits_page_timeslot.html')

@main_bp.route('/subjects', methods=['GET'])
@login_required
def get_subjects():
    class_name = request.args.get('class_name')
    semester = request.args.get('semester')

    subjects, _ = fetch_data(class_name, semester, session['school_id'])
    return jsonify(subjects)

@main_bp.route('/save_priorities', methods=['POST'])
@login_required
def save_priorities():
    # Deprecated/Used by old flow? Keep for now or refactor.
    # The new flow sends priorities directly to /generate.
    return jsonify({"success": True})

@main_bp.route('/generate_setup')
@login_required
def generate_setup():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM class WHERE school_id = %s", (session['school_id'],))
    classes = cursor.fetchall()
    db.close()
    return render_template('generate.html', classes=classes)

def get_daily_slots(config, include_break=False):
    start_str = config.get('start_time')
    end_str = config.get('end_time')
    duration_min = int(config.get('lecture_duration', 60))
    break_start_str = config.get('break_start')
    break_duration_min = int(config.get('break_duration', 0))

    start_time = datetime.strptime(start_str, "%H:%M")
    end_time = datetime.strptime(end_str, "%H:%M")
    
    break_start = None
    break_end = None
    if break_start_str:
        break_start = datetime.strptime(break_start_str, "%H:%M")
        break_end = break_start + timedelta(minutes=break_duration_min)

    slots = []
    current = start_time
    
    while current + timedelta(minutes=duration_min) <= end_time:
        slot_end = current + timedelta(minutes=duration_min)
        
        # Check if this slot overlaps with break
        if break_start and break_end:
            # Simplified: If current equals break start, it's a break slot.
            if current >= break_start and current < break_end:
                 if include_break:
                     slots.append({'time': current.strftime("%H:%M:%S"), 'type': 'break'})
                 current = break_end # Skip past break
                 continue
            
            # Also handle if slot end > break start (overlap from left)
            if current < break_start and slot_end > break_start:
                 current = break_end
                 continue

        if include_break:
             slots.append({'time': current.strftime("%H:%M:%S"), 'type': 'lecture'})
        else:
             slots.append(current.strftime("%H:%M:%S"))
             
        current = slot_end
        
    return slots

@main_bp.route('/generate', methods=['POST'])
@login_required
def generate_timetable():
    try:
        data = request.json
        class_name = data.get('class_name')
        semester = data.get('semester')
        priorities = data.get('priorities', {})
        # credits = data.get('credits') # Ignore frontend credits, fetch from DB

        school_id = session['school_id']

        # Fetch subjects and their Credits from DB
        db = connect_db()
        cursor = db.cursor(dictionary=True, buffered=True)
        
        # Get class_id
        cursor.execute("SELECT class_id FROM class WHERE class_name = %s AND school_id = %s", (class_name, school_id))
        res = cursor.fetchone()
        if not res:
             return jsonify({"error": f"Class '{class_name}' not found"}), 404
        class_id = res['class_id']

        # Fetch subjects with credits
        cursor.execute("SELECT subject_name, credits FROM subject WHERE class_id = %s AND semester = %s AND school_id = %s", (class_id, semester, school_id))
        subject_rows = cursor.fetchall()
        db.close()

        if not subject_rows:
            return jsonify({"error": "No subjects found for this class and semester"}), 400

        subjects = [row['subject_name'] for row in subject_rows]
        credits = {row['subject_name']: row['credits'] for row in subject_rows}
        
        # Ensure priorities exist for all subjects
        final_priorities = {}
        for sub in subjects:
            final_priorities[sub] = int(priorities.get(sub, 1))

        time_config = session.get('time_config')
        if time_config:
            # Generate dynamic timeslots
            timeslots = get_daily_slots(time_config, include_break=False)
            print(f"Generated dynamic timeslots: {timeslots}")
        else:
             return jsonify({"error": "Time configuration not found. Please re-login."}), 400

        total_available_slots = len(timeslots) * 6  
        total_required_slots = sum(credits.values())

        if total_required_slots > total_available_slots:
            return jsonify({"error": f"Not enough timeslots! Required: {total_required_slots}, Available: {total_available_slots}"}), 400

        db = connect_db()
        cursor = db.cursor(buffered=True)

        # Get course_id (Simplified: assuming one course per class/school logic from before)
        # We need it for INSERT.
        cursor.execute("SELECT course_id FROM course WHERE school_id = %s LIMIT 1", (school_id,))
        res = cursor.fetchone()
        course_id = res[0] if res else 1

        # 🔹 Synch Timeslots to DB (Ensure they exist)
        # We need to ensure every generated timeslot exists in DB to have a time_id
        # We will build a map of {timeslot_string: time_id}
        timeslot_id_map = {}
        
        for slot in timeslots:
            cursor.execute("SELECT time_id FROM timeslot WHERE timeslot = %s", (slot,))
            result = cursor.fetchone()
            if result:
                timeslot_id_map[slot] = result[0]
            else:
                # Insert new slot
                print(f"Inserting new timeslot: {slot}")
                cursor.execute("INSERT INTO timeslot (timeslot, type_of_class) VALUES (%s, 'lecture')", (slot,))
                timeslot_id_map[slot] = cursor.lastrowid
        
        db.commit() # Commit new timeslots

        # 🔹 Clear existing timetable for this class and semester to prevent self-conflicts
        print(f"DEBUG: Clearing existing timetable for Class {class_id}, Semester {semester}")
        cursor.execute("DELETE FROM timetable WHERE class_id = %s", (class_id,)) 
        db.commit()

        # 🔹 Fetch existing teacher schedules (excluding what we just deleted)
        cursor.execute("SELECT teacher_id, time_id FROM timetable")
        existing_teacher_schedules = cursor.fetchall()

        teacher_schedule_map = {}
        for teacher_id, time_id in existing_teacher_schedules:
            if teacher_id not in teacher_schedule_map:
                teacher_schedule_map[teacher_id] = set()
            teacher_schedule_map[teacher_id].add(time_id)

        # 🔹 Generate timetable
        timetable = genetic_algorithm(subjects, timeslots, final_priorities, credits)

        # 🔹 Convert `timedelta` timeslot values to strings before querying
        # And ensure we have a working list we can modify/filter
        for entry in timetable:
            if isinstance(entry["timeslot"], timedelta):  
                entry["timeslot"] = str(entry["timeslot"])  # Convert to "HH:MM:SS" format

        # session['timetable'] = timetable  <-- Don't save yet!

        saved_timetable = [] # Only keep entries that are actually saved

        print(f"DEBUG: Starting DB insertion loop. Total generated entries: {len(timetable)}")

        for entry in timetable:
            cursor.execute(
                "SELECT subject_id, teacher_id FROM subject WHERE subject_name = %s AND class_id = %s AND semester = %s",
                (entry["subject"], class_id, semester)
            )
            result = cursor.fetchone()
            if result:
                subject_id, teacher_id = result
                
                # 🔹 Retrieve correct `time_id` from our map or DB
                # Since we synced earlier, we can try to use our map for efficiency or query DB safely
                # Let's use the DB query as original logic, but now satisfied knowing it exists.
                # Actually, using map is safer if we just inserted it.
                
                time_id = timeslot_id_map.get(entry["timeslot"])
                
                if not time_id:
                     # Fallback query
                    cursor.execute("SELECT time_id FROM timeslot WHERE timeslot = %s", (entry["timeslot"],))
                    time_id_result = cursor.fetchone()
                    if time_id_result:
                         time_id = int(time_id_result[0])

                if not time_id:
                    print(f"DEBUG: Skipping entry {entry['subject']}: No time_id found for {entry['timeslot']}")
                    continue  # Skip if no time_id found

                # 🔹 Check for teacher conflict
                if teacher_id in teacher_schedule_map and time_id in teacher_schedule_map[teacher_id]:
                    # print(f"⚠️ Conflict detected: Teacher {teacher_id} is already assigned at timeslot {time_id}.")

                    # Find an alternative timeslot
                    # Available = All generated dynamic timeslots - Teacher's busy ID mapping
                    # We have IDs in teacher_schedule_map. We need IDs of our current dynamic set.
                    
                    current_slot_ids = set(timeslot_id_map.values())
                    busy_ids = teacher_schedule_map.get(teacher_id, set())
                    
                    available_ids = current_slot_ids - busy_ids
                    
                    if available_ids:
                        new_time_id = list(available_ids)[0] # Pick first available
                        # Find string for this ID
                        new_timeslot_str = next((k for k, v in timeslot_id_map.items() if v == new_time_id), None)
                        
                        if new_time_id:
                            # print(f"✅ Rescheduled to available timeslot {new_time_id} ({new_timeslot_str}).")
                            time_id = new_time_id
                            entry['timeslot'] = new_timeslot_str
                        else:
                             print(f"DEBUG: Skipping entry {entry['subject']}: Logic Error finding string for ID {new_time_id}")
                             continue
                    else:
                        print(f"DEBUG: Skipping entry {entry['subject']}: No available timeslot for teacher {teacher_id}")
                        continue

                # Insert into timetable and update teacher's occupied slots
                # UPDATE: Included 'day' in insert
                cursor.execute(
                    "INSERT INTO timetable (teacher_id, subject_id, class_id, course_id, time_id, day, school_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (teacher_id, subject_id, class_id, course_id, time_id, entry['day'], school_id)
                )
                if teacher_id not in teacher_schedule_map:
                    teacher_schedule_map[teacher_id] = set()
                teacher_schedule_map[teacher_id].add(time_id)
                
                # Add to saved list
                saved_timetable.append(entry)
            else:
                 print(f"DEBUG: Skipping entry {entry['subject']}: Subject not found in DB for Class {class_id} Sem {semester}")

        db.commit()
        cursor.close()
        db.close()

        print(f"DEBUG: Finished insertion. Saved {len(saved_timetable)} entries.")
        session['timetable'] = saved_timetable # Update session with only the successfully saved entries

        return jsonify({"success": True, "redirect": "/final_timetable"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/save_modified_timetable', methods=['POST'])
def save_modified_timetable():
    try:
        data = request.json
        updated_timetable = data.get('timetable')

        if not updated_timetable:
            return jsonify({"error": "Timetable data is missing"}), 400

        session['timetable'] = updated_timetable  # Save in session
        
        # NOTE: Ideally we should update the DB here too, but for now we keep session persistent for immediate modifications.
        # If user wants permanent modifications to stick, we'd need another DB update logic here.
        # For 'view timetable', it will pull the *initial* generated one unless we update DB here.
        # Let's assume for now the user wants to fetch the generated one. 
        # If they modify, it's currently only in session. The user didn't explicitly ask for modification persistence, just 'view' persistence.

        return jsonify({"message": "Timetable updated successfully!", "redirect": "/final_timetable"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/final_timetable')
def final_timetable():
    timetable_data = session.get('timetable', [])
    structured_timetable = {}
    
    # Populate structured timetable
    for entry in timetable_data:
        day = entry['day']
        timeslot = entry['timeslot']
        subject = entry['subject']
        structured_timetable[(day, timeslot)] = subject

    # Visualization Slots
    time_config = session.get('time_config')
    if time_config:
         visual_slots = get_daily_slots(time_config, include_break=True)
    else:
         # Fallback logic if no config (e.g. legacy or simple view)
         # We just use the unique timeslots found in data
         used_slots = set(entry['timeslot'] for entry in timetable_data)
         visual_slots = [{'time': slot, 'type': 'lecture'} for slot in sorted(used_slots)]

    return render_template("final_timetable.html", timetable=structured_timetable, timeslots=visual_slots)

@main_bp.route('/modify_timetable', methods=['GET', 'POST'])
def modify_timetable():
    if request.method == 'GET':
        timetable = session.get('timetable', [])
        # modify_timetable also needs to know about full slots ideally?
        # For now keep it simple, it loads just lecture slots usually.
        
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT timeslot FROM timeslot")
        timeslots = [str(row[0]) for row in cursor.fetchall()]
        db.close()

        return render_template("modify_timetable.html", timetable=timetable, timeslots=timeslots)

    elif request.method == 'POST':
        try:
            data = request.json
            updated_timetable = data.get('timetable')

            if not updated_timetable:
                return jsonify({"error": "Timetable data is missing"}), 400

            session['timetable'] = updated_timetable  

            return jsonify({"message": "Timetable updated successfully!", "redirect": "/final_timetable"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
@main_bp.route('/view_timetable')
def view_timetable():
    return render_template("view_timetable.html")

@main_bp.route('/get_timetable', methods=['GET'])
def get_timetable():
    try:
        class_name = request.args.get('class_name')
        semester = request.args.get('semester')

        if not class_name or not semester:
            return jsonify({"error": "Missing class name or semester"}), 400

        # Try fetching from DB first
        timetable_db, timeslots_list = get_timetable_by_class(class_name, semester, session['school_id'])
        
        # If we have time_config in session (and checks pass), use it for better visualization?
        # But this might be risky if viewing a DIFFERENT class.
        # So for View, strictly use the DB data + whatever gaps we can infer OR just simple list.
        # But wait, if user wants to see breaks in View, we need that info.
        # Since we don't store "Break" in DB, we can't show it in View Timetable safely unless we assume global break or current session config.
        # Let's use session config if available for now (Assuming user is verifying their work).
        
        visual_slots = []
        time_config = session.get('time_config')
        if time_config:
             print("Using session time_config for View.")
             # Assume this config applies to what we are viewing (Verification Phase)
             visual_slots = get_daily_slots(time_config, include_break=True)
        else:
             # Just map the raw strings to objects
             visual_slots = [{'time': t, 'type': 'lecture'} for t in timeslots_list]

        if timetable_db:
             return jsonify({"timetable": timetable_db, "visual_slots": visual_slots})

        # Fallback to session
        timetable_data = session.get('timetable', [])
        if not timetable_data:
            return jsonify({"error": "No timetable found for this class. Please generate it first."}), 404

        structured_timetable = {}
        for entry in timetable_data:
            day = entry['day']
            timeslot = entry['timeslot']
            subject = entry['subject']
            structured_timetable[f"{day}_{timeslot}"] = subject
            
        return jsonify({"timetable": structured_timetable, "visual_slots": visual_slots})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
