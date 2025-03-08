from flask import Flask, render_template, request, jsonify, session
import mysql.connector
import random
import json
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="aanand",
        database="timetabledb"
    )

# Fetch subjects and timeslots
def fetch_data(class_name, semester):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT class_id FROM class WHERE class_name = %s", (class_name,))
    class_id = cursor.fetchone()

    if class_id is None:
        return [], []

    class_id = class_id[0]
    cursor.execute("SELECT subject_name FROM subject WHERE class_id = %s AND semester = %s", (class_id, semester))
    subjects = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT timeslot FROM timeslot")
    timeslots = [row[0] for row in cursor.fetchall()]

    db.close()
    return subjects, timeslots

# Genetic Algorithm for First Allocation
def genetic_algorithm(subjects, timeslots, priorities, credits, generations=100, population_size=20):
    def fitness(schedule):
        score = 0
        subject_counts = {s: 0 for s in subjects}
        
        for entry in schedule:
            subject_counts[entry['subject']] += 1
            score += (5 - priorities[entry['subject']])  

        for subject, count in subject_counts.items():
            if count == credits[subject]:  
                score += 10  
            else:
                score -= 10  

        return score

    def create_individual():
        individual = []
        used_slots = set()
        
        for subject in subjects:
            required_lectures = credits[subject]
            for _ in range(required_lectures):
                while True:
                    day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
                    timeslot = random.choice(timeslots)
                    if (day, timeslot) not in used_slots:
                        used_slots.add((day, timeslot))
                        individual.append({"day": day, "timeslot": timeslot, "subject": subject})
                        break
        return individual

    population = [create_individual() for _ in range(population_size)]

    for _ in range(generations):
        population = sorted(population, key=fitness, reverse=True)
        next_gen = population[:10]
        
        for _ in range(10):
            p1, p2 = random.sample(next_gen, 2)
            child = p1[:len(p1)//2] + p2[len(p2)//2:]
            next_gen.append(child)

        population = next_gen

    return sorted(population, key=fitness, reverse=True)[0]

@app.route('/')
def home():
    return render_template('index_prior_page_timeslot.html')

@app.route('/credits')
def credits_page():
    return render_template('credits_page_timeslot.html')

@app.route('/subjects', methods=['GET'])
def get_subjects():
    class_name = request.args.get('class_name')
    semester = request.args.get('semester')

    subjects, _ = fetch_data(class_name, semester)
    return jsonify(subjects)

@app.route('/save_priorities', methods=['POST'])
def save_priorities():
    try:
        data = request.json
        class_name = data.get("class_name")
        semester = data.get("semester")
        priorities = data.get("priorities")

        if not class_name or not semester or not priorities:
            return jsonify({"error": "Missing data"}), 400

        session['class_name'] = class_name
        session['semester'] = semester
        session['priorities'] = priorities

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_timetable():
    try:
        data = request.json
        class_name = data.get('class_name')
        semester = data.get('semester')
        credits = data.get('credits')

        subjects, timeslots = fetch_data(class_name, semester)

        total_available_slots = len(timeslots) * 6  
        total_required_slots = sum(credits.values())

        if total_required_slots > total_available_slots:
            return jsonify({"error": f"Not enough timeslots! Required: {total_required_slots}, Available: {total_available_slots}"}), 400

        priorities = session.get('priorities', {subject: 1 for subject in subjects})  

        db = connect_db()
        cursor = db.cursor()

        # 🔹 Fetch existing teacher schedules
        cursor.execute("SELECT teacher_id, time_id FROM timetable")
        existing_teacher_schedules = cursor.fetchall()

        teacher_schedule_map = {}
        for teacher_id, time_id in existing_teacher_schedules:
            if teacher_id not in teacher_schedule_map:
                teacher_schedule_map[teacher_id] = set()
            teacher_schedule_map[teacher_id].add(time_id)

        # 🔹 Generate timetable
        timetable = genetic_algorithm(subjects, timeslots, priorities, credits)

        # 🔹 Convert `timedelta` timeslot values to strings before querying
        for entry in timetable:
            if isinstance(entry["timeslot"], timedelta):  
                entry["timeslot"] = str(entry["timeslot"])  # Convert to "HH:MM:SS" format

        session['timetable'] = timetable  

        # Get class_id and course_id
        cursor.execute("SELECT class_id FROM class WHERE class_name = %s", (class_name,))
        class_id = cursor.fetchone()[0]

        cursor.execute("SELECT course_id FROM course WHERE course_name = 'BSc'")
        course_id = cursor.fetchone()[0]

        for entry in timetable:
            cursor.execute(
                "SELECT subject_id, teacher_id FROM subject WHERE subject_name = %s AND class_id = %s AND semester = %s",
                (entry["subject"], class_id, semester)
            )
            result = cursor.fetchone()
            if result:
                subject_id, teacher_id = result
                
                # 🔹 Retrieve correct `time_id` from `timeslot` table
                cursor.execute("SELECT time_id FROM timeslot WHERE timeslot = %s", (entry["timeslot"],))
                time_id_result = cursor.fetchone()

                if time_id_result:
                    time_id = int(time_id_result[0])  # Ensure `time_id` is an integer
                else:
                    print(f"⚠️ No matching time_id found for timeslot '{entry['timeslot']}'. Skipping entry.")
                    continue  # Skip if no time_id found

                # 🔹 Check for teacher conflict
                if teacher_id in teacher_schedule_map and time_id in teacher_schedule_map[teacher_id]:
                    print(f"⚠️ Conflict detected: Teacher {teacher_id} is already assigned at timeslot {time_id}.")

                    # Find an alternative timeslot
                    available_timeslots = set(timeslots) - teacher_schedule_map.get(teacher_id, set())
                    if available_timeslots:
                        new_time_id = None
                        for ts in available_timeslots:
                            cursor.execute("SELECT time_id FROM timeslot WHERE timeslot = %s", (ts,))
                            new_time_id_result = cursor.fetchone()
                            if new_time_id_result:
                                new_time_id = int(new_time_id_result[0])
                                break  # Use the first available slot

                        if new_time_id:
                            print(f"✅ Rescheduled to available timeslot {new_time_id}.")
                            time_id = new_time_id
                        else:
                            print(f"❌ No available timeslot found for teacher {teacher_id}. Skipping entry.")
                            continue  

                # Insert into timetable and update teacher's occupied slots
                cursor.execute(
                    "INSERT INTO timetable (teacher_id, subject_id, class_id, course_id, time_id) VALUES (%s, %s, %s, %s, %s)",
                    (teacher_id, subject_id, class_id, course_id, time_id)
                )
                if teacher_id not in teacher_schedule_map:
                    teacher_schedule_map[teacher_id] = set()
                teacher_schedule_map[teacher_id].add(time_id)

        db.commit()
        cursor.close()
        db.close()

        return jsonify({"success": True, "redirect": "/modify_timetable"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/save_modified_timetable', methods=['POST'])
def save_modified_timetable():
    try:
        data = request.json
        updated_timetable = data.get('timetable')

        if not updated_timetable:
            return jsonify({"error": "Timetable data is missing"}), 400

        session['timetable'] = updated_timetable  # Save in session

        return jsonify({"message": "Timetable updated successfully!", "redirect": "/final_timetable"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/final_timetable')
def final_timetable():
    timetable_data = session.get('timetable', [])

    structured_timetable = {}
    timeslots = set()

    for entry in timetable_data:
        day = entry['day']
        timeslot = entry['timeslot']
        subject = entry['subject']
        structured_timetable[(day, timeslot)] = subject
        timeslots.add(timeslot)

    sorted_timeslots = sorted(timeslots)

    return render_template("final_timetable.html", timetable=structured_timetable, timeslots=sorted_timeslots)

@app.route('/modify_timetable', methods=['GET', 'POST'])
def modify_timetable():
    if request.method == 'GET':
        timetable = session.get('timetable', [])
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT timeslot FROM timeslot")
        timeslots = [row[0] for row in cursor.fetchall()]
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
        
@app.route('/view_timetable')
def view_timetable():
    timetable_data = session.get('timetable', [])

    structured_timetable = {}
    timeslots = set()

    for entry in timetable_data:
        day = entry['day']
        timeslot = entry['timeslot']
        subject = entry['subject']
        structured_timetable[(day, timeslot)] = subject
        timeslots.add(timeslot)

    sorted_timeslots = sorted(timeslots)

    return render_template("view_timetable.html", timetable=structured_timetable, timeslots=sorted_timeslots)

@app.route('/get_timetable', methods=['GET'])
def get_timetable():
    try:
        class_name = request.args.get('class_name')
        semester = request.args.get('semester')

        if not class_name or not semester:
            return jsonify({"error": "Missing class name or semester"}), 400

        # Retrieve timetable stored in session
        timetable_data = session.get('timetable', [])

        if not timetable_data:
            return jsonify({"error": "No timetable found. Please generate it first."}), 404

        structured_timetable = {}
        timeslots = set()

        for entry in timetable_data:
            day = entry['day']
            timeslot = entry['timeslot']
            subject = entry['subject']
            
            structured_timetable[f"{day}_{timeslot}"] = subject
            timeslots.add(timeslot)

        return jsonify({"timetable": structured_timetable, "timeslots": sorted(timeslots)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
