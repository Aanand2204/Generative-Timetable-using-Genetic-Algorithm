from flask import Flask, render_template, request, jsonify, session
import mysql.connector
import random
import json

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

        timetable = genetic_algorithm(subjects, timeslots, priorities, credits)

        for entry in timetable:
            entry["timeslot"] = str(entry["timeslot"])

        session['timetable'] = timetable  

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

if __name__ == '__main__':
    app.run(debug=True)
