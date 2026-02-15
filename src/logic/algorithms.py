
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
            
            subject_counts = {}
            for i in range(len(entries)):
                entry = entries[i]
                subj = entry['subject']
                subject_counts[subj] = subject_counts.get(subj, 0) + 1
                
                # Reward consecutive placement for high priority subjects
                if i > 0:
                    prev_entry = entries[i-1]
                    if prev_entry['subject'] == subj and subj in high_priority_subjects:
                        # Significant bonus for consecutive high-priority lectures
                        score += 100 * priorities.get(subj, 1)
                
                # General priority reward (place high priority subjects anyway)
                score += priorities.get(subj, 1) * 5

            for subj, count in subject_counts.items():
                if count > 2:
                    # Penalty for too many lectures of the same subject on one day
                    score -= (count - 2) * 50
                elif count == 2 and subj not in high_priority_subjects:
                    # Minor penalty for non-high priority subjects having 2 lectures
                    score -= 20
                    
        return score

    best_schedule = []
    best_score = float('-inf')

    # Increase attempts to find a valid schedule if constraints are tight
    attempts = max(population_size * 10, 200) 
    
    for _ in range(attempts):
        current_schedule = []
        available_slots = all_slots.copy()
        current_credits = credits.copy()
        
        # 1. Attempt to place consecutive blocks for High Priority subjects
        shuffled_high_priority = list(high_priority_subjects)
        random.shuffle(shuffled_high_priority)
        
        for subj in shuffled_high_priority:
            if current_credits.get(subj, 0) < 2:
                continue
            
            # Find a day with 2 consecutive VALID slots
            shuffled_days = days.copy()
            random.shuffle(shuffled_days)
            
            placed_block = False
            for day in shuffled_days:
                # Find all available slots for this day
                day_slots_in_pool = [i for i, x in enumerate(available_slots) if x[0] == day]
                if not day_slots_in_pool:
                    continue
                
                time_idx_map = {t: i for i, t in enumerate(timeslots)}
                valid_day_indices = []
                for idx in day_slots_in_pool:
                    _, time_val = available_slots[idx]
                    if (day, time_val) not in invalid_slots.get(subj, set()):
                        valid_day_indices.append((idx, time_idx_map[time_val]))
                
                valid_day_indices.sort(key=lambda x: x[1]) # Sort by time
                
                # Find consecutive pair
                for k in range(len(valid_day_indices) - 1):
                    idx1, t_ord1 = valid_day_indices[k]
                    idx2, t_ord2 = valid_day_indices[k+1]
                    
                    if t_ord2 == t_ord1 + 1:
                        # Found consecutive!
                        current_schedule.append({"day": day, "timeslot": timeslots[t_ord1], "subject": subj})
                        current_schedule.append({"day": day, "timeslot": timeslots[t_ord2], "subject": subj})
                        
                        # Remove from available (higher index first to keep indices valid)
                        indices_to_remove = sorted([idx1, idx2], reverse=True)
                        for r_idx in indices_to_remove:
                            available_slots.pop(r_idx)
                        
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
            
            for i, (day, time) in enumerate(available_slots):
                if (day, time) not in constraints:
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
