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
        return [], [], {}

    class_id = class_id[0]
    
    cursor.execute("SELECT subject_id, subject_name FROM subject WHERE class_id = %s AND semester = %s", (class_id, semester))
    subjects = cursor.fetchall()

    cursor.execute("SELECT time_id, timeslot FROM timeslot")
    timeslots = [time[1] for time in cursor.fetchall()]
    
    db.close()
    
    credits = {subject_name: random.randint(2, 5) for _, subject_name in subjects}
    return subjects, timeslots, credits

import random

# Genetic Algorithm for Timetable Scheduling
import random

def genetic_algorithm(subjects, timeslots, credits, days_order, population_size=10, generations=50):
    def create_individual():
        """Creates a timetable ensuring exact credits per subject."""
        timetable = {subject: [] for _, subject in subjects}
        available_slots = {day: timeslots[:] for day in days_order}  # Keep track of available timeslots per day
        subject_counts = {subject: 0 for _, subject in subjects}  # Track subject assignments

        # Ensure first lecture of each day is allocated
        for day in days_order:
            if available_slots[day]:
                first_timeslot = available_slots[day].pop(0)  # Reserve first slot
                highest_priority_subject = sorted(subjects, key=lambda s: credits[s[1]])[0][1]
                timetable[highest_priority_subject].append((day, first_timeslot))
                subject_counts[highest_priority_subject] += 1

        # Assign remaining slots ensuring strict credit-based allocation
        shuffled_subjects = sorted(subjects, key=lambda s: credits[s[1]])  # Prioritize subjects with lower priority values
        random.shuffle(shuffled_subjects)

        for _, subject in shuffled_subjects:
            while subject_counts[subject] < credits[subject]:
                for day in days_order:
                    if available_slots[day]:  # Ensure slots are available
                        timeslot = available_slots[day].pop(0)
                        timetable[subject].append((day, timeslot))
                        subject_counts[subject] += 1
                        break  # Move to next subject after assigning

        return timetable

    def fitness(individual):
        """Evaluates the timetable based on constraints."""
        score = 0
        seen_slots = set()
        subject_count = {subject: 0 for subject in individual}

        for subject, slots in individual.items():
            subject_count[subject] = len(slots)

            # ✅ Enforce exact credit allocation
            if subject_count[subject] == credits[subject]:
                score += 10  # Reward exact credit matches
            else:
                score -= abs(subject_count[subject] - credits[subject]) * 5  # Penalize mismatches

            # ✅ Prevent duplicate timeslot assignments
            for slot in slots:
                if slot not in seen_slots:
                    seen_slots.add(slot)
                    score += 1  # Reward unique placements
                else:
                    score -= 2  # Penalize overlaps

        return score

    def crossover(parent1, parent2):
        """Performs crossover between two parents."""
        child = {}
        for subject in parent1:
            child[subject] = random.choice([parent1[subject], parent2[subject]])
        return child

    def mutate(individual):
        """Mutates an individual to explore better solutions."""
        if random.random() < 0.1:  # 10% mutation chance
            subject1, subject2 = random.sample(list(individual.keys()), 2)
            if individual[subject1] and individual[subject2]:
                i, j = random.randint(0, len(individual[subject1]) - 1), random.randint(0, len(individual[subject2]) - 1)
                individual[subject1][i], individual[subject2][j] = individual[subject2][j], individual[subject1][i]
        return individual

    # Initialize population
    population = [create_individual() for _ in range(population_size)]
    
    for _ in range(generations):
        # Evaluate fitness & select the best individuals
        population.sort(key=fitness, reverse=True)
        new_population = population[:population_size // 2]  # Keep top 50%
        
        # Generate new individuals via crossover & mutation
        while len(new_population) < population_size:
            parent1, parent2 = random.sample(new_population, 2)
            child = mutate(crossover(parent1, parent2))
            new_population.append(child)
        
        population = new_population  # Replace old population with new
    
    # Return the best timetable
    return max(population, key=fitness)




# Allocate timeslots using Genetic Algorithm
def allocate_weekly_timeslots(class_name, semester, credits, priorities):
    subjects, timeslots, _ = fetch_data(class_name, semester)

    if not subjects or not timeslots:
        return None

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    sorted_subjects = sorted(subjects, key=lambda s: priorities[s[1]])

    best_timetable = genetic_algorithm(sorted_subjects, timeslots, credits, days_order)

    seen_slots = set()
    subject_count = {subject[1]: 0 for subject in sorted_subjects}  # Track assigned counts
    df = []

    for i, day in enumerate(days_order):
        if i < len(sorted_subjects):
            subject = sorted_subjects[i][1]  
            if subject_count[subject] < credits[subject]:  # ✅ Ensure exact assignment
                first_timeslot = timeslots[0]  
                df.append([day, str(first_timeslot), subject])
                seen_slots.add((day, first_timeslot))
                subject_count[subject] += 1  # ✅ Track assigned count

    for subject, slots in best_timetable.items():
        for day, timeslot in slots:
            if (day, timeslot) not in seen_slots and subject_count[subject] < credits[subject]:
                df.append([day, str(timeslot), subject])
                seen_slots.add((day, timeslot))
                subject_count[subject] += 1  # ✅ Track count

    df = pd.DataFrame(df, columns=["Day", "Timeslot", "Subject"])
    df.sort_values(by=["Day", "Timeslot"], inplace=True)
    df["Day"] = pd.Categorical(df["Day"], categories=days_order, ordered=True)

    df_pivot = df.pivot(index="Timeslot", columns="Day", values="Subject").reset_index()
    df_pivot.replace({np.nan: "-"}, inplace=True)

    return df_pivot.to_dict(orient='records')



@app.route('/')
def home():
    return render_template('index_prior_subjects.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        class_name = request.form.get('class_name')
        semester = request.form.get('semester')
        credits = request.form.get('credits')
        priorities = request.form.get('priorities')

        if not class_name or not semester or not credits or not priorities:
            return jsonify({"error": "Missing class name, semester, credits, or priorities."}), 400

        try:
            credits = json.loads(credits)  
            priorities = json.loads(priorities)  
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format."}), 400

        timetable = allocate_weekly_timeslots(class_name, semester, credits, priorities)

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
    
    subjects, _, _ = fetch_data(class_name, semester)
    
    return jsonify([subject[1] for subject in subjects])  # Return list of subject names

if __name__ == '__main__':
    app.run(debug=True)
