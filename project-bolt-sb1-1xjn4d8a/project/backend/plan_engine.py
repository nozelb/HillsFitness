from typing import Dict, List, Any, Optional
from models import WorkoutDay, Exercise

def generate_workout_plan(
    user_data: Dict[str, Any],
    image_analysis: Optional[Dict[str, Any]],
    goal: str,
    days_per_week: int = 4
) -> List[WorkoutDay]:
    """
    Generate evidence-based workout plan following ACSM guidelines
    """
    
    # Base exercise database
    exercises_db = {
        "chest": [
            {"name": "Push-ups", "equipment": "bodyweight"},
            {"name": "Bench Press", "equipment": "barbell"},
            {"name": "Dumbbell Press", "equipment": "dumbbell"},
            {"name": "Incline Press", "equipment": "barbell"},
        ],
        "back": [
            {"name": "Pull-ups", "equipment": "bodyweight"},
            {"name": "Bent-over Row", "equipment": "barbell"},
            {"name": "Lat Pulldown", "equipment": "machine"},
            {"name": "Deadlift", "equipment": "barbell"},
        ],
        "shoulders": [
            {"name": "Overhead Press", "equipment": "barbell"},
            {"name": "Lateral Raises", "equipment": "dumbbell"},
            {"name": "Face Pulls", "equipment": "cable"},
            {"name": "Pike Push-ups", "equipment": "bodyweight"},
        ],
        "arms": [
            {"name": "Bicep Curls", "equipment": "dumbbell"},
            {"name": "Tricep Dips", "equipment": "bodyweight"},
            {"name": "Close-grip Push-ups", "equipment": "bodyweight"},
            {"name": "Hammer Curls", "equipment": "dumbbell"},
        ],
        "legs": [
            {"name": "Squats", "equipment": "bodyweight"},
            {"name": "Lunges", "equipment": "bodyweight"},
            {"name": "Romanian Deadlift", "equipment": "barbell"},
            {"name": "Calf Raises", "equipment": "bodyweight"},
        ],
        "core": [
            {"name": "Plank", "equipment": "bodyweight"},
            {"name": "Mountain Climbers", "equipment": "bodyweight"},
            {"name": "Russian Twists", "equipment": "bodyweight"},
            {"name": "Dead Bug", "equipment": "bodyweight"},
        ]
    }
    
    # Determine training parameters based on goal
    if goal == "lose_fat":
        rep_range = "12-15"
        rest_time = 45
        sets = 3
    elif goal == "gain_muscle":
        rep_range = "8-12"
        rest_time = 60
        sets = 4
    elif goal == "recomposition":
        rep_range = "10-12"
        rest_time = 60
        sets = 3
    else:  # maintenance
        rep_range = "10-12"
        rest_time = 60
        sets = 3
    
    # Generate workout split based on days per week
    if days_per_week == 3:
        split = [
            {"day": "Day 1", "muscle_groups": ["chest", "shoulders", "arms"]},
            {"day": "Day 2", "muscle_groups": ["back", "arms"]},
            {"day": "Day 3", "muscle_groups": ["legs", "core"]},
        ]
    elif days_per_week == 4:
        split = [
            {"day": "Day 1", "muscle_groups": ["chest", "shoulders"]},
            {"day": "Day 2", "muscle_groups": ["back", "arms"]},
            {"day": "Day 3", "muscle_groups": ["legs", "core"]},
            {"day": "Day 4", "muscle_groups": ["chest", "arms"]},
        ]
    else:  # 5 days
        split = [
            {"day": "Day 1", "muscle_groups": ["chest", "shoulders"]},
            {"day": "Day 2", "muscle_groups": ["back"]},
            {"day": "Day 3", "muscle_groups": ["legs"]},
            {"day": "Day 4", "muscle_groups": ["shoulders", "arms"]},
            {"day": "Day 5", "muscle_groups": ["legs", "core"]},
        ]
    
    workout_plan = []
    
    for day_info in split:
        exercises = []
        total_duration = 0
        
        for muscle_group in day_info["muscle_groups"]:
            # Select 2-3 exercises per muscle group
            selected_exercises = exercises_db[muscle_group][:2]
            
            for exercise_info in selected_exercises:
                exercise = Exercise(
                    name=exercise_info["name"],
                    sets=sets,
                    reps=rep_range,
                    rest_seconds=rest_time,
                    notes=f"Focus on controlled movement and proper form"
                )
                exercises.append(exercise)
                
                # Estimate duration (sets * (work_time + rest_time))
                work_time = 30  # Average time per set
                exercise_duration = sets * (work_time + rest_time) / 60  # Convert to minutes
                total_duration += exercise_duration
        
        workout_day = WorkoutDay(
            day=day_info["day"],
            muscle_groups=day_info["muscle_groups"],
            exercises=exercises,
            estimated_duration_minutes=int(total_duration)
        )
        workout_plan.append(workout_day)
    
    return workout_plan