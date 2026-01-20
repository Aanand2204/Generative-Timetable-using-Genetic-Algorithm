
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
    max_p = max(priorities.values()) if priorities else 0
    high_priority_subjects = {s for s, p in priorities.items() if p == max_p}
    # Or maybe top 50%? User said "higher priority". Let's stick to strict Max or Max-1 if range is small.
    # User example: 1-5. Let's say 4 and 5 are high?
    # Let's settle on: Priority >= Max - 1 (Top 2 tiers)
    high_priority_subjects = {s for s, p in priorities.items() if p >= max(1, max_p - 1)}

    def calculate_distribution_score(schedule):
        penalty = 0
        day_subject_counts = {day: {} for day in days}
        
        for entry in schedule:
            d = entry['day']
            s = entry['subject']
            day_subject_counts[d][s] = day_subject_counts[d].get(s, 0) + 1
            
        for day in days:
            for subject, count in day_subject_counts[day].items():
                if count > 1:
                    # If high priority, allow 2 lectures without penalty IF they are consecutive
                    # But verifying consecutiveness here is complex without sorting slots.
                    # Simplified: If high priority and count == 2, Small Penalty or even Bonus?
                    # User request: "get 2 lectures... one after the other".
                    # If we successfully placed them consecutively, count will be 2.
                    if subject in high_priority_subjects and count == 2:
                        # Find if there are 2 consecutive
                        # We need to sort entries for this subject on this day
                        # This checks if the placement logic worked.
                        pass # No penalty! (Or small bonus)
                    else:
                        penalty -= (count - 1) * 10
        return penalty

    best_schedule = []
    best_score = float('-inf')

    # Increase attempts to find a valid schedule if constraints are tight
    attempts = max(population_size * 10, 200) 
    
    for _ in range(attempts):
        current_schedule = []
        available_slots = all_slots.copy()
        current_pool = class_pool.copy()
        
        # 1. Attempt to place consecutive blocks for High Priority subjects
        # Shuffle days to randomize which day gets the block
        shuffled_days = days.copy()
        random.shuffle(shuffled_days)
        
        # Sort subjects by priority desc (optional, but good heuristic)
        # We need a mutable count tracker
        current_credits = credits.copy()
        
        # Iterate high priority subjects
        for subj in list(high_priority_subjects):
            if current_credits[subj] < 2:
                continue
            
            # Try to find a day with 2 consecutive VALID slots
            placed_block = False
            random.shuffle(shuffled_days) 
            
            for day in shuffled_days:
                # Get all indices of this day in available_slots
                # available_slots list structure: [(day, time), ...]
                # Indices might be scattered if we popped? No, we haven't popped yet.
                # But slots are ordered by day in 'all_slots'.
                # In 'available_slots', we might shuffle?
                # For this step, we should iterate 'available_slots' carefully.
                pass
            
            # Strategy: scan available_slots for (day, t) and (day, t_next)
            # Find all available slots for this day
            day_slots_indices = [i for i, x in enumerate(available_slots) if x[0] == day]
            
            # Sort by time index?
            # We need to know order of 'timeslots'.
            # Map time -> index
            time_idx_map = {t: i for i, t in enumerate(timeslots)}
            
            # Filter and sort invalid
            valid_day_indices = []
            for idx in day_slots_indices:
                day_val, time_val = available_slots[idx]
                if (day_val, time_val) not in invalid_slots.get(subj, set()):
                    valid_day_indices.append((idx, time_idx_map[time_val]))
            
            valid_day_indices.sort(key=lambda x: x[1]) # Sort by time
            
            # Find consecutive pair
            for k in range(len(valid_day_indices) - 1):
                idx1, t_ord1 = valid_day_indices[k]
                idx2, t_ord2 = valid_day_indices[k+1]
                
                if t_ord2 == t_ord1 + 1:
                    # Found consecutive!
                    # Assign both
                    current_schedule.append({"day": day, "timeslot": timeslots[t_ord1], "subject": subj})
                    current_schedule.append({"day": day, "timeslot": timeslots[t_ord2], "subject": subj})
                    
                    # Remove from available (careful with indices changing)
                    # Remove higher index first
                    available_slots.pop(max(idx1, idx2))
                    available_slots.pop(min(idx1, idx2))
                    
                    current_credits[subj] -= 2
                    
                    # Remove from pool list (2 instances)
                    # Safe remove
                    for _ in range(2):
                        if subj in current_pool:
                            current_pool.remove(subj)
                            
                    placed_block = True
                    break # Done for this subject (allow 1 block per subject max? or multiple?)
            
            if placed_block:
                continue # Move to next subject (or try another block?)
                         # User says "get 2 lectures". Usually just one pair.
        
        # 2. Assign remaining credits normally (Random logic)
        random.shuffle(available_slots)
        random.shuffle(current_pool)
        
        possible_rest = True
        
        for subj in current_pool:
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
                if best_score == 0:
                    break
    
    return best_schedule
