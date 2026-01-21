
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
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
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/manage_teachers', methods=['GET', 'POST'])
@login_required
def manage_teachers():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    edit_teacher = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            teacher_id = request.form.get('teacher_id')
            try:
                # Cascade DELETE: 
                # 1. Remove from timetable
                cursor.execute("DELETE FROM timetable WHERE teacher_id = %s AND school_id = %s", (teacher_id, session['school_id']))
                # 2. Remove from allocated_timeslots (if applicable)
                cursor.execute("DELETE FROM allocated_timeslots WHERE teacher_id = %s AND school_id = %s", (teacher_id, session['school_id']))
                # 3. Remove assigned subjects (Constraint causing the issue)
                cursor.execute("DELETE FROM subject WHERE teacher_id = %s AND school_id = %s", (teacher_id, session['school_id']))
                # 4. Finally delete the teacher
                cursor.execute("DELETE FROM teacher WHERE teacher_id = %s AND school_id = %s", (teacher_id, session['school_id']))
                
                db.commit()
                flash('Teacher and their assigned subjects deleted successfully!', 'success')
            except Exception as e:
                flash(f'Error deleting teacher: {str(e)}', 'error')
                
        elif action == 'update':
            teacher_id = request.form.get('teacher_id')
            name = request.form.get('teacher_name')
            try:
                cursor.execute("UPDATE teacher SET teacher_name = %s WHERE teacher_id = %s AND school_id = %s", (name, teacher_id, session['school_id']))
                db.commit()
                flash('Teacher updated successfully!', 'success')
                return redirect(url_for('main.manage_teachers'))
            except Exception as e:
                flash(f'Error updating teacher: {str(e)}', 'error')

        else: # Add
            try:
                name = request.form.get('teacher_name')
                if name:
                    cursor.execute("INSERT INTO teacher (teacher_name, school_id) VALUES (%s, %s)", (name, session['school_id']))
                    db.commit()
                    flash('Teacher added successfully!', 'success')
            except Exception as e:
                flash(f'Error adding teacher: {str(e)}', 'error')

    # GET: Check for edit_id
    edit_id = request.args.get('edit_id')
    if edit_id:
        cursor.execute("SELECT * FROM teacher WHERE teacher_id = %s AND school_id = %s", (edit_id, session['school_id']))
        edit_teacher = cursor.fetchone()
            
    cursor.execute("SELECT * FROM teacher WHERE school_id = %s", (session['school_id'],))
    teachers = cursor.fetchall()
    db.close()
    return render_template('manage_teachers.html', teachers=teachers, edit_teacher=edit_teacher)

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
        
    edit_class = None
    edit_subject = None

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'add_class':
                class_name = request.form.get('class_name')
                if class_name:
                    cursor.execute("INSERT INTO class (class_name, school_id) VALUES (%s, %s)", (class_name, school_id))
                    db.commit()
                    flash('Class added successfully!', 'success')
            
            elif action == 'update_class':
                class_id = request.form.get('class_id')
                class_name = request.form.get('class_name')
                cursor.execute("UPDATE class SET class_name = %s WHERE class_id = %s AND school_id = %s", (class_name, class_id, school_id))
                db.commit()
                flash('Class updated successfully!', 'success')
                return redirect(url_for('main.manage_subjects'))

            elif action == 'delete_class':
                class_id = request.form.get('class_id')
                # Manual cascade delete for subjects
                cursor.execute("DELETE FROM subject WHERE class_id = %s AND school_id = %s", (class_id, school_id))
                cursor.execute("DELETE FROM class WHERE class_id = %s AND school_id = %s", (class_id, school_id))
                db.commit()
                flash('Class and its subjects deleted successfully!', 'success')
            
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
                flash('Subject added successfully!', 'success')

            elif action == 'update_subject':
                subject_id = request.form.get('subject_id')
                subject_name = request.form.get('subject_name')
                class_id = request.form.get('class_id')
                teacher_id = request.form.get('teacher_id')
                credits = request.form.get('credits') 
                semester = request.form.get('semester')
                
                cursor.execute("""
                    UPDATE subject 
                    SET subject_name=%s, class_id=%s, teacher_id=%s, semester=%s, credits=%s
                    WHERE subject_id=%s AND school_id=%s
                """, (subject_name, class_id, teacher_id, semester, credits, subject_id, school_id))
                db.commit()
                flash('Subject updated successfully!', 'success')
                return redirect(url_for('main.manage_subjects'))

            elif action == 'delete_subject':
                subject_id = request.form.get('subject_id')
                cursor.execute("DELETE FROM subject WHERE subject_id = %s AND school_id = %s", (subject_id, school_id))
                db.commit()
                flash('Subject deleted successfully!', 'success')

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            pass

    # Check for Edit Mode
    edit_class_id = request.args.get('edit_class_id')
    if edit_class_id:
        cursor.execute("SELECT * FROM class WHERE class_id = %s AND school_id = %s", (edit_class_id, school_id))
        edit_class = cursor.fetchone()

    edit_subject_id = request.args.get('edit_subject_id')
    if edit_subject_id:
         cursor.execute("SELECT * FROM subject WHERE subject_id = %s AND school_id = %s", (edit_subject_id, school_id))
         edit_subject = cursor.fetchone()

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
    return render_template('manage_subjects.html', classes=classes, teachers=teachers, subjects=subjects, edit_class=edit_class, edit_subject=edit_subject)

@main_bp.route('/manage_timings', methods=['GET', 'POST'])
@login_required
def manage_timings():
    if request.method == 'POST':
        start_time_str = request.form.get('start_time')
        lecture_duration = int(request.form.get('lecture_duration'))
        num_lectures = int(request.form.get('num_lectures'))
        break_after = int(request.form.get('break_after'))
        break_duration = int(request.form.get('break_duration') or 0)

        # Calculate times based on inputs
        start_time = datetime.strptime(start_time_str, "%H:%M")
        
        # Calculate Break Start
        # Break starts after 'break_after' lectures
        # If break_after is 0, no break.
        break_start_time = None
        break_start_str = None
        
        current_time = start_time
        
        # We need to simulate the day to find exact break start and end time
        # Actually easier: Break Start = Start + (Break After * Lecture Duration)
        if break_after > 0:
            break_start_time = start_time + timedelta(minutes=break_after * lecture_duration)
            break_start_str = break_start_time.strftime("%H:%M")
        
        # Calculate School End Time
        # Length = (Num Lectures * Duration) + (Break Duration if Applicable)
        total_minutes = num_lectures * lecture_duration
        if break_after > 0 and break_after < num_lectures:
             total_minutes += break_duration
             
        end_time = start_time + timedelta(minutes=total_minutes)
        end_time_str = end_time.strftime("%H:%M")

        db = connect_db()
        cursor = db.cursor()
        
        try:
            sql = """
                UPDATE schools 
                SET start_time = %s, end_time = %s, lecture_duration = %s, break_start_time = %s, break_duration = %s
                WHERE school_id = %s
            """
            cursor.execute(sql, (start_time_str, end_time_str, lecture_duration, break_start_str, break_duration, session['school_id']))
            db.commit()
            
            # Update session config
            session['time_config'] = {
                'start_time': start_time_str,
                'end_time': end_time_str,
                'lecture_duration': lecture_duration,
                'break_start': break_start_str,
                'break_duration': break_duration,
                'num_lectures': num_lectures,
                'break_after': break_after
            }
            flash('Timings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating timings: {str(e)}', 'error')
        finally:
            db.close()
            
        return redirect(url_for('main.manage_timings'))

    # GET request
    config = session.get('time_config')
    
    # If config is missing 'num_lectures' (migrating from old config), try to derive it
    if config and 'num_lectures' not in config:
        try:
            s_time = datetime.strptime(config.get('start_time'), "%H:%M")
            e_time = datetime.strptime(config.get('end_time'), "%H:%M")
            l_dur = int(config.get('lecture_duration', 60))
            b_dur = int(config.get('break_duration', 0))
            b_start_str = config.get('break_start')
            
            total_duration = (e_time - s_time).seconds / 60
            
            # If break exists
            if b_start_str:
                b_start = datetime.strptime(b_start_str, "%H:%M")
                # Lectures before break
                lectures_before = (b_start - s_time).seconds / 60 / l_dur
                
                # Remaining time after break
                # (School End - Break End) / Lecture Duration
                b_end = b_start + timedelta(minutes=b_dur)
                lectures_after = (e_time - b_end).seconds / 60 / l_dur
                
                config['num_lectures'] = int(lectures_before + lectures_after)
                config['break_after'] = int(lectures_before)
            else:
                config['num_lectures'] = int(total_duration / l_dur)
                config['break_after'] = 0
                
        except Exception:
            pass # Keep defaults or what's there
            
    return render_template('manage_timings.html', config=config)

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

def perform_timetable_generation(class_name, semester, priorities, school_id):
    """
    Helper function to perform the actual timetable generation logic.
    Returns: (saved_timetable, error_message)
    """
    try:
        # Fetch subjects and their Credits from DB
        db = connect_db()
        cursor = db.cursor(dictionary=True, buffered=True)
        
        # Get class_id
        cursor.execute("SELECT class_id FROM class WHERE class_name = %s AND school_id = %s", (class_name, school_id))
        res = cursor.fetchone()
        if not res:
            db.close()
            return None, f"Class '{class_name}' not found"
        class_id = res['class_id']

        # Get course_id
        cursor.execute("SELECT course_id FROM course WHERE school_id = %s LIMIT 1", (school_id,))
        course_res = cursor.fetchone()
        course_id = course_res['course_id'] if course_res else 1

        # 🔹 Generate timetable with constraints
        # 1. Map Subject -> Teacher -> Busy Slots
        # We need to know which slots are invalid for each subject based on its teacher
        invalid_slots = {} 
        
        # Build map of time_id -> time_string for easy lookup
        # We need this to convert DB time_ids back to strings the algo understands
        # We can build it from timeslots list assuming they map to IDs we just synced?
        # Better: Query DB for all timeslots to get ID->String map
        cursor.execute("SELECT time_id, timeslot FROM timeslot")
        all_db_slots = cursor.fetchall() # list of (id, timedelta)
        
        id_to_time_map = {}
        for row in all_db_slots:
            # Format timedelta to HH:MM:SS
            t_str = str(row['timeslot'])
            if len(t_str) == 7: # 9:00:00 -> 09:00:00
                 t_str = "0" + t_str
            id_to_time_map[row['time_id']] = t_str

        # Re-fetch subjects including teacher_id
        cursor.execute("SELECT subject_name, credits, teacher_id FROM subject WHERE class_id = %s AND semester = %s AND school_id = %s", (class_id, semester, school_id))
        subject_rows = cursor.fetchall()
        
        subjects = [row['subject_name'] for row in subject_rows]
        credits = {row['subject_name']: row['credits'] for row in subject_rows}
        # Re-map priorities
        final_priorities = {}
        for sub in subjects:
            final_priorities[sub] = int(priorities.get(sub, 1))

        # 🔹 Retrieve Time Config and Generate Timeslots
        time_config = session.get('time_config')
        if not time_config:
             db.close()
             return None, "Time configuration not found. Please re-login."

        # Generate dynamic timeslots
        timeslots = get_daily_slots(time_config, include_break=False)
        
        # 🔹 Sync Timeslots to DB (Ensure they exist and get IDs)
        # We prefer using the dynamic slots generated from config.
        # But we need their IDs.
        timeslot_id_map = {} # Map string -> ID
        
        for slot in timeslots:
            # Check if this exact string exists in DB map we built earlier
             # We built id_to_time_map earlier: ID -> String
             # Let's verify against that or just query/insert.
             
             # Reverse lookup in existing map?
             found_id = None
             for tid, tstr in id_to_time_map.items():
                 if tstr == slot:
                     found_id = tid
                     break
            
             if found_id:
                 timeslot_id_map[slot] = found_id
             else:
                 # Insert new if not found (Consistency check)
                 cursor.execute("INSERT INTO timeslot (timeslot, type_of_class) VALUES (%s, 'lecture')", (slot,))
                 timeslot_id_map[slot] = cursor.lastrowid
                 # Update reverse map too just in case
                 id_to_time_map[cursor.lastrowid] = slot
        
        db.commit() # Commit any new slots

        # 🔹 Clear existing timetable for this class to prevent self-conflict
        cursor.execute("DELETE FROM timetable WHERE class_id = %s", (class_id,))
        db.commit()

        # 🔹 RE-BUILD teacher_schedule_map with DAYS
        cursor.execute("SELECT teacher_id, time_id, day FROM timetable")
        existing_schedule_rows = cursor.fetchall()
        
        # Map: teacher_id -> set of (day, time_string)
        teacher_busy_map = {}
        for r_tid, r_timeid, r_day in existing_schedule_rows:
            if r_tid not in teacher_busy_map:
                teacher_busy_map[r_tid] = set()
            
            # Convert time_id to string
            t_str = id_to_time_map.get(r_timeid)
            if t_str and r_day:
                teacher_busy_map[r_tid].add((r_day, t_str))

        # Now populate invalid_slots for our algorithm
        for row in subject_rows:
            subj_name = row['subject_name']
            t_id = row['teacher_id']
            if t_id in teacher_busy_map:
                invalid_slots[subj_name] = teacher_busy_map[t_id]

        # DEBUG LOGGING SETUP
        import logging
        logging.basicConfig(filename='debug_gen.log', level=logging.DEBUG)
        
        logging.info(f"DEBUG: derived invalid_slots for constraints: {invalid_slots}")

        logging.info(f"STARTING GENERATION: Class={class_name}, Sem={semester}, School={school_id}")
        
        # 🔹 Generate timetable
        timetable = genetic_algorithm(subjects, timeslots, final_priorities, credits, invalid_slots=invalid_slots)
        logging.info(f"Algorithm produced {len(timetable)} entries")

        # 🔹 Convert `timedelta` timeslot values to strings before querying
        for entry in timetable:
            if isinstance(entry["timeslot"], timedelta):  
                entry["timeslot"] = str(entry["timeslot"])  

        saved_timetable = [] 
        logging.info(f"DEBUG: Starting DB insertion loop. Total generated entries: {len(timetable)}")

        for entry in timetable:
            # Ensure semester is int for DB query consistency if column is int
            semester_int = int(semester)
            cursor.execute(
                "SELECT subject_id, teacher_id FROM subject WHERE subject_name = %s AND class_id = %s AND semester = %s",
                (entry["subject"], class_id, semester_int)
            )
            result = cursor.fetchone()
            if result:
                subject_id = result['subject_id']
                teacher_id = result['teacher_id']
                
                time_id = timeslot_id_map.get(entry["timeslot"])
                
                if not time_id:
                     # Fallback query
                    cursor.execute("SELECT time_id FROM timeslot WHERE timeslot = %s", (entry["timeslot"],))
                    time_id_result = cursor.fetchone()
                    if time_id_result:
                         time_id = int(time_id_result[0])
                
                if not time_id:
                    logging.warning(f"DEBUG: Skipping entry {entry['subject']}: No time_id found for {entry['timeslot']}")
                    continue 
                
                # Check for existing entry to prevent duplicates (though we deleted valid ones earlier)
                # But we deleted WHERE class_id = ... so we should be clear.
                
                # Insert into timetable
                try:
                    cursor.execute(
                        "INSERT INTO timetable (teacher_id, subject_id, class_id, course_id, time_id, day, school_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (teacher_id, subject_id, class_id, course_id, time_id, entry['day'], school_id)
                    )
                    saved_timetable.append(entry)
                except Exception as e:
                    logging.error(f"Insert Failed: {e}")
                    # Do not append to saved_timetable if insert failed
            else:
                 logging.warning(f"DEBUG: Skipping entry {entry['subject']}: Subject not found in DB for Class {class_id} Sem {semester_int} (Orig: {semester})")

        db.commit()
        cursor.close()
        db.close()
        return saved_timetable, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)


@main_bp.route('/generate', methods=['POST'])
@login_required
def generate_timetable():
    try:
        data = request.json
        class_name = data.get('class_name')
        semester = data.get('semester')
        priorities = data.get('priorities', {})
        school_id = session['school_id']

        saved_timetable, error = perform_timetable_generation(class_name, semester, priorities, school_id)
        
        if error:
             return jsonify({"error": error}), 500

        print(f"DEBUG: Finished insertion. Saved {len(saved_timetable)} entries.")
        
        session['timetable'] = saved_timetable
        
        # Save context for regeneration UX
        session['generation_context'] = {
            'class_name': class_name,
            'semester': semester,
            'priorities': priorities # Store priorities for quick regenerate
        }

        return jsonify({"message": "Timetable generated successfully!", "redirect": "/final_timetable"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/regenerate_quick')
@login_required
def regenerate_quick():
    context = session.get('generation_context')
    if not context:
        flash("No recent generation context found. Please generate normally first.", "warning")
        return redirect(url_for('main.generate_setup'))
    
    class_name = context.get('class_name')
    semester = context.get('semester')
    priorities = context.get('priorities')
    school_id = session['school_id']
    
    saved_timetable, error = perform_timetable_generation(class_name, semester, priorities, school_id)
    
    if error:
        flash(f"Regeneration failed: {error}", "error")
        return redirect(url_for('main.final_timetable'))
        
    session['timetable'] = saved_timetable
    flash("Timetable regenerated successfully!", "success")
    return redirect(url_for('main.final_timetable'))

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
    context = session.get('generation_context', {})
    
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
         visual_slots = [{'time': slot, 'type': 'lecture'} for slot in sorted(set(entry['timeslot'] for entry in timetable_data))]

    return render_template("final_timetable.html", 
                           timetable=structured_timetable, 
                           timeslots=visual_slots,
                           class_name=context.get('class_name'),
                           semester=context.get('semester'))

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
        
        # Public Access Logic: Resolve School ID by Username
        school_username = request.args.get('username')
        school_id = None
        
        if school_username:
             db = connect_db()
             cursor = db.cursor(dictionary=True)
             cursor.execute("SELECT school_id FROM schools WHERE username = %s", (school_username,))
             school = cursor.fetchone()
             db.close()
             
             if school:
                 school_id = school['school_id']
             else:
                 return jsonify({"error": "School not found. Please check the username."}), 404
        
        # Fallback to session if available (Admin viewing)
        if not school_id:
            school_id = session.get('school_id')

        if not school_id:
            # No username provided and not logged in
            return jsonify({"error": "Please provide the School's Admin Username."}), 400

        if not class_name or not semester:
            return jsonify({"error": "Missing class name or semester"}), 400

        # Try fetching from DB first
        timetable_db, timeslots_list = get_timetable_by_class(class_name, semester, school_id)
        
        # If we have time_config in session (and checks pass), use it for better visualization?
        # For public access, we don't have session['time_config'].
        # We should fetch time config for the school from DB if possible, or just rely on DB slots.
        
        visual_slots = []
        time_config = session.get('time_config')
        
        if not time_config and school_id:
             # Fetch config from DB for public view
             db = connect_db()
             cursor = db.cursor(dictionary=True)
             cursor.execute("SELECT * FROM schools WHERE school_id = %s", (school_id,))
             school_config = cursor.fetchone()
             db.close()
             
             if school_config:
                 # Construct minimal config object
                 time_config = {
                    'start_time': str(school_config['start_time']),
                    'end_time': str(school_config['end_time']),
                    'lecture_duration': school_config['lecture_duration'],
                    'break_start': str(school_config['break_start_time']) if school_config['break_start_time'] else None,
                    'break_duration': school_config['break_duration']
                 }

        if time_config:
             # Assume this config applies to what we are viewing
             visual_slots = get_daily_slots(time_config, include_break=True)
        else:
             # Just map the raw strings to objects
             visual_slots = [{'time': t, 'type': 'lecture'} for t in timeslots_list]

        if timetable_db:
             return jsonify({"timetable": timetable_db, "visual_slots": visual_slots})

        # Fallback to session (Only if logged in / admin viewing own generation)
        # Students won't have session['timetable']
        timetable_data = session.get('timetable', [])
        if not timetable_data:
            return jsonify({"error": "No timetable found for this class."}), 404

        structured_timetable = {}
        for entry in timetable_data:
            day = entry['day']
            timeslot = entry['timeslot']
            subject = entry['subject']
            structured_timetable[f"{day}_{timeslot}"] = subject
            
        return jsonify({"timetable": structured_timetable, "visual_slots": visual_slots})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
