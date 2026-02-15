
import random

def genetic_algorithm(subjects, timeslots, priorities, credits, invalid_slots=None, generations=100, population_size=20):
    """
    Generates a timetable that strictly respects credits and teacher availability constraints.
    Prioritizes placing 2 consecutive lectures for high priority subjects.
    invalid_slots: dict {subject: set([(day, time_str), ...])}
    """
    if invalid_slots is None:
        invalid_slots = {}
        
    class_pool = []
    for subject, count in credits.items():
        class_pool.extend([subject] * count)
        
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    all_slots = []
    for day in days:
        for slot in timeslots:
            all_slots.append((day, slot))

    # Identify high priority subjects (top tier)
    # Identify high priority subjects (priority 4 and 5, or just the top tier)
    max_p = max(priorities.values()) if priorities else 0
    high_priority_subjects = {s for s, p in priorities.items() if p >= max(1, max_p - 1)}

    def calculate_distribution_score(schedule):
        score = 0
        day_schedules = {day: [] for day in days}
        for entry in schedule:
            day_schedules[entry['day']].append(entry)
        
        time_idx_map = {t: i for i, t in enumerate(timeslots)}
        
        for day, entries in day_schedules.items():
            # Sort by time to check for consecutive slots
            entries.sort(key=lambda x: time_idx_map.get(x['timeslot'], 0))
            
            subject_slots = {} # subj -> list of slot indices
            for i in range(len(entries)):
                entry = entries[i]
                subj = entry['subject']
                slot_idx = time_idx_map.get(entry['timeslot'], 0)
                
                if subj not in subject_slots:
                    subject_slots[subj] = []
                subject_slots[subj].append(slot_idx)
                
                # Reward consecutive placement for high priority subjects
                if i > 0:
                    prev_entry = entries[i-1]
                    prev_idx = time_idx_map.get(prev_entry['timeslot'])
                    
                    if prev_entry['subject'] == subj and subj in high_priority_subjects and slot_idx == prev_idx + 1:
                        # Bonus for truly consecutive high-priority lectures
                        score += 20 * priorities.get(subj, 1)
                
                # General priority reward
                score += priorities.get(subj, 1) * 2

            # Reward variety: High bonus for number of unique subjects on a day
            score += len(subject_slots) * 100

            for subj, indices in subject_slots.items():
                count = len(indices)
                if count > 2:
                    # HEAVY penalty for exceeding daily limit
                    score -= (count - 2) * 500
                elif count == 2 and subj not in high_priority_subjects:
                    # Minor penalty for non-high priority subjects having 2 lectures
                    score -= 20
                
                # 🔹 Penalize if multiple lectures on same day are NOT contiguous
                if count >= 2:
                    indices.sort()
                    if (indices[-1] - indices[0]) != (count - 1):
                        score -= 100 * count
                
                # Reward spreading: Small bonus for each day a subject appears
                score += 30
                    
        return score

    best_schedule = []
    best_score = float('-inf')

    # Increase attempts to find a valid schedule if constraints are tight
    attempts = max(population_size * 10, 200) 
    
    for _ in range(attempts):
        current_schedule = []
        available_slots = all_slots.copy()
        current_credits = credits.copy()
        
        # Ensure ML & AI credits are handled as 4
        if 'ML & AI' in current_credits:
            current_credits['ML & AI'] = 4

        shuffled_high_priority = list(high_priority_subjects)
        random.shuffle(shuffled_high_priority)
        
        time_idx_map = {t: i for i, t in enumerate(timeslots)} # Ensure time_idx_map is available here

        # 1. Attempt to place ONE consecutive double for High Priority subjects
        for subj in shuffled_high_priority:
            if current_credits.get(subj, 0) < 2:
                continue
            
            # Find a day with 2 consecutive VALID slots
            shuffled_days = days.copy()
            random.shuffle(shuffled_days)
            
            placed_block = False
            for day in shuffled_days:
                # Find all available slots for this day that are valid
                day_slots = []
                for i, (d, t) in enumerate(available_slots):
                    if d == day and (d, t) not in invalid_slots.get(subj, set()):
                        day_slots.append({'index': i, 'time': t})
                
                if len(day_slots) < 2:
                    continue
                
                # Sort by time index
                day_slots.sort(key=lambda x: time_idx_map.get(x['time'], 0))
                
                # Find consecutive pair
                for k in range(len(day_slots) - 1):
                    s1 = day_slots[k]
                    s2 = day_slots[k+1]
                    
                    if time_idx_map[s1['time']] + 1 == time_idx_map[s2['time']]:
                        # Found a pair!
                        current_schedule.append({"day": day, "timeslot": s1['time'], "subject": subj})
                        current_schedule.append({"day": day, "timeslot": s2['time'], "subject": subj})
                        
                        # Remove from available (higher index first)
                        indices_to_remove = sorted([s1['index'], s2['index']], reverse=True)
                        available_slots.pop(indices_to_remove[0])
                        available_slots.pop(indices_to_remove[1])
                        
                        current_credits[subj] -= 2
                        placed_block = True
                        break
                
                if placed_block:
                    break # Move to next priority subject
        
        # 2. Assign remaining credits normally (Random logic)
        remaining_pool = []
        for subj, count in current_credits.items():
            remaining_pool.extend([subj] * count)
        
        random.shuffle(remaining_pool)
        random.shuffle(available_slots)
        
        possible_rest = True
        for subj in remaining_pool:
            assigned = False
            constraints = invalid_slots.get(subj, set())
            
            # Count existing assignments for this subject on each day
            subject_day_counts = {}
            for entry in current_schedule:
                if entry['subject'] == subj:
                    subject_day_counts[entry['day']] = subject_day_counts.get(entry['day'], 0) + 1

            for i, (day, time) in enumerate(available_slots):
                # Strict Limit: At most 2 lectures per day
                if subject_day_counts.get(day, 0) < 2 and (day, time) not in constraints:
                    current_schedule.append({"day": day, "timeslot": time, "subject": subj})
                    available_slots.pop(i)
                    assigned = True
                    break
            
            if not assigned:
                possible_rest = False
                break
        
        if possible_rest:
            score = calculate_distribution_score(current_schedule)
            if score > best_score:
                best_score = score
                best_schedule = current_schedule
    
    return best_schedule
