from flask import Flask, render_template, request, jsonify, session
import mysql.connector
import pandas as pd
import numpy as np
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session storage

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="aanand",
        database="timetabledb"
    )

# Fetch subjects and timeslots from the database
def fetch_data(class_name, semester):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT class_id FROM class WHERE class_name = %s", (class_name,))
    class_id = cursor.fetchone()

    if class_id is None:
        return [], []

    class_id = class_id[0]
    cursor.execute("SELECT subject_id, subject_name FROM subject WHERE class_id = %s AND semester = %s", (class_id, semester))
    subjects = cursor.fetchall()

    cursor.execute("SELECT time_id, timeslot FROM timeslot")
    timeslots = [time[1] for time in cursor.fetchall()]

    db.close()
    return subjects, timeslots

# Allocate timeslots based on priorities and credits
def allocate_weekly_timeslots(class_name, semester, priorities, credits):
    subjects, timeslots = fetch_data(class_name, semester)
    
    if not subjects or not timeslots:
        return None

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    # Sort subjects by priority
    sorted_subjects = sorted(subjects, key=lambda s: priorities[s[1]])

    # Initialize structures
    timetable = {subject[1]: [] for subject in sorted_subjects}
    available_slots = {day: timeslots[:] for day in days_order}
    subject_counts = {subject[1]: 0 for subject in sorted_subjects}
    subject_days = {subject[1]: set() for subject in sorted_subjects}
    daily_count = {day: 0 for day in days_order}

    # Step 1: Ensure each day gets at least 2 lectures
    day_index = 0
    for _ in range(len(days_order) * 2):  # 6 days * 2 minimum slots
        for subject in sorted_subjects:
            if subject_counts[subject[1]] < credits[subject[1]]:
                day = days_order[day_index % len(days_order)]
                if available_slots[day] and daily_count[day] < 2:
                    timeslot = available_slots[day].pop(0)
                    timetable[subject[1]].append((day, timeslot))
                    subject_counts[subject[1]] += 1
                    subject_days[subject[1]].add(day)
                    daily_count[day] += 1
                    day_index += 1

    # Step 2: Distribute remaining lectures
    for _ in range(sum(credits.values()) - (len(days_order) * 2)):
        for subject in sorted_subjects:
            if subject_counts[subject[1]] < credits[subject[1]]:
                for day in days_order:
                    if available_slots[day]:
                        timeslot = available_slots[day].pop(0)
                        timetable[subject[1]].append((day, timeslot))
                        subject_counts[subject[1]] += 1
                        break

    # Convert timetable to DataFrame for structured output
    df = []
    for subject, slots in timetable.items():
        for day, timeslot in slots:
            df.append([day, str(timeslot), subject])

    df = pd.DataFrame(df, columns=["Day", "Timeslot", "Subject"])
    df["Day"] = pd.Categorical(df["Day"], categories=days_order, ordered=True)
    df.sort_values(by=["Day", "Timeslot"], inplace=True)

    # Pivot to structured format
    df_pivot = df.pivot(index="Timeslot", columns="Day", values="Subject").reset_index()
    df_pivot.replace({np.nan: "-"}, inplace=True)

    return df_pivot.to_dict(orient='records')

@app.route('/')
def home():
    return render_template('index_prior_page.html')

@app.route('/save_priorities', methods=['POST'])
def save_priorities():
    data = request.json
    session['class_name'] = data.get("class_name")
    session['semester'] = data.get("semester")
    session['priorities'] = data.get("priorities")
    return jsonify({"success": True})

@app.route('/credits')
def credits_page():
    return render_template('credits_page.html')

@app.route('/get_priorities')
def get_priorities():
    if 'priorities' not in session:
        return jsonify({"error": "No priorities found"}), 400
    return jsonify({"subjects": list(session['priorities'].keys())})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        priorities = session.get('priorities', {})
        class_name = session.get('class_name')
        semester = session.get('semester')

        if not priorities or not class_name or not semester:
            return jsonify({"error": "Missing priorities, class name, or semester."}), 400

        credits = data.get("credits", {})
        if len(credits) != len(priorities):  # Ensure sum of credits matches total subjects
            return jsonify({"error": "Invalid credit assignment. Total must match number of subjects."}), 400

        timetable = allocate_weekly_timeslots(class_name, semester, priorities, credits)
        if timetable is None:
            return jsonify({"error": "Failed to generate timetable."}), 400

        return jsonify({"message": "Timetable generated successfully!", "timetable": timetable})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subjects', methods=['GET'])
def get_subjects():
    class_name = request.args.get('class_name')
    semester = request.args.get('semester')
    
    subjects, _ = fetch_data(class_name, semester)
    
    return jsonify([subject[1] for subject in subjects])  # Return list of subject names

if __name__ == '__main__':
    app.run(debug=True)
