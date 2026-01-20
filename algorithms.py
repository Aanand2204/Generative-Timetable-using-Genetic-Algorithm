
import random

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
