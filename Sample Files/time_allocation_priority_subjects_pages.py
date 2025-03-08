from flask import Flask, render_template, request, jsonify
import mysql.connector
import random
import pandas as pd
import numpy as np
import json

app = Flask(__name__)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="aanand",
        database="timetabledb"
    )

# Fetch data from the database based on class_name and semester
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

# Allocate timeslots based on priorities
def allocate_weekly_timeslots(class_name, semester, priorities):
    subjects, timeslots = fetch_data(class_name, semester)

    if not subjects or not timeslots:
        return None

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    sorted_subjects = sorted(subjects, key=lambda s: priorities[s[1]])

    timetable = {}
    for subject in sorted_subjects:
        timetable[subject[1]] = []

    available_slots = {day: timeslots[:] for day in days_order}
    
    for subject in sorted_subjects:
        for day in days_order:
            if available_slots[day]:
                timeslot = available_slots[day].pop(0)
                timetable[subject[1]].append((day, timeslot))

    df = []
    for subject, slots in timetable.items():
        for day, timeslot in slots:
            df.append([day, str(timeslot), subject])

    df = pd.DataFrame(df, columns=["Day", "Timeslot", "Subject"])
    df.sort_values(by=["Day", "Timeslot"], inplace=True)
    df["Day"] = pd.Categorical(df["Day"], categories=days_order, ordered=True)

    df_pivot = df.pivot(index="Timeslot", columns="Day", values="Subject").reset_index()
    df_pivot.replace({np.nan: "-"}, inplace=True)

    return df_pivot.to_dict(orient='records')

@app.route('/')
def home():
    return render_template('index_prior_subjects_pages.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        class_name = request.form.get('class_name')
        semester = request.form.get('semester')
        priorities = request.form.get('priorities')

        if not class_name or not semester or not priorities:
            return jsonify({"error": "Missing class name, semester, or priorities."}), 400

        try:
            priorities = json.loads(priorities)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format."}), 400

        timetable = allocate_weekly_timeslots(class_name, semester, priorities)

        if timetable is None:
            return jsonify({"error": "Failed to generate timetable."}), 400

        return jsonify(timetable)

    except Exception as e:
        print("🔥 ERROR in /generate:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/subjects', methods=['GET'])
def get_subjects():
    class_name = request.args.get('class_name')
    semester = request.args.get('semester')
    
    subjects, _ = fetch_data(class_name, semester)
    
    return jsonify([subject[1] for subject in subjects])  # Return list of subject names

if __name__ == '__main__':
    app.run(debug=True)
