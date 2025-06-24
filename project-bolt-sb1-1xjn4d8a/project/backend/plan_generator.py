# plan_generator_v2.py - Enhanced 4-week plan generation

from typing import Dict, List, Any
from datetime import date, timedelta
import copy

def generate_4_week_plan(
    user_profile: Dict[str, Any],
    current_metrics: Dict[str, Any],
    image_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a complete 4-week progressive workout and diet plan
    """
    
    # Base workout template
    base_week = generate_base_week(
        goal=user_profile['primary_fitness_goal'],
        days_per_week=user_profile['preferred_training_days'],
        experience_level=determine_experience_level(user_profile)
    )
    
    # Generate 4 progressive weeks
    workout_weeks = []
    for week_num in range(1, 5):
        week_plan = apply_weekly_progression(
            base_week=copy.deepcopy(base_week),
            week_number=week_num,
            goal=user_profile['primary_fitness_goal']
        )
        workout_weeks.append({
            'week_number': week_num,
            'workouts': week_plan,
            'focus': get_weekly_focus(week_num)
        })
    
    # Generate matching diet plan
    diet_plan = generate_diet_plan(
        current_metrics=current_metrics,
        goal=user_profile['primary_fitness_goal'],
        activity_level=user_profile['activity_level'],
        workout_days=user_profile['preferred_training_days']
    )
    
    # Define progression rules
    progression_rules = {
        'fat_loss': {
            'volume_increase': 5,  # 5% increase per week
            'intensity_stable': True,
            'cardio_progression': 'duration'
        },
        'muscle_gain': {
            'volume_increase': 10,  # 10% increase weeks 1-3
            'deload_week_4': True,
            'weight_progression': '2.5-5%'
        },
        'recomposition': {
            'volume_increase': 7.5,
            'intensity_waves': True,
            'hybrid_approach': True
        }
    }
    
    return {
        'workout_weeks': workout_weeks,
        'diet_plan': diet_plan,
        'progression_rules': progression_rules[user_profile['primary_fitness_goal']],
        'equipment_needed': detect_required_equipment(workout_weeks),
        'estimated_session_duration': calculate_session_duration(base_week)
    }

def apply_weekly_progression(base_week: Dict, week_number: int, goal: str) -> List[Dict]:
    """
    Apply progressive overload based on week and goal
    """
    progression_multipliers = {
        1: 1.0,    # Base week
        2: 1.05,   # 5% increase
        3: 1.10,   # 10% increase  
        4: 0.7 if goal == 'muscle_gain' else 1.15  # Deload or peak
    }
    
    multiplier = progression_multipliers[week_number]
    
    for workout in base_week:
        for exercise in workout['exercises']:
            if week_number == 4 and goal == 'muscle_gain':
                # Deload week - reduce volume, maintain intensity
                exercise['sets'] = max(2, int(exercise['sets'] * 0.7))
            else:
                # Progressive overload
                if 'reps' in exercise and isinstance(exercise['reps'], str):
                    # Handle rep ranges like "8-12"
                    low, high = map(int, exercise['reps'].split('-'))
                    new_low = int(low * multiplier)
                    new_high = int(high * multiplier)
                    exercise['reps'] = f"{new_low}-{new_high}"
                
                # Add weight progression note
                if week_number > 1:
                    exercise['progression_note'] = f"Increase weight by 2.5-5% from week {week_number-1}"
    
    return base_week

def handle_plan_regeneration(
    original_plan: Dict[str, Any],
    user_comments: str,
    substitution_rules: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Regenerate plan based on user feedback
    """
    # Parse user comments for exercise substitutions
    requested_swaps = parse_exercise_swaps(user_comments)
    
    new_plan = copy.deepcopy(original_plan)
    
    for week in new_plan['workout_weeks']:
        for workout in week['workouts']:
            for i, exercise in enumerate(workout['exercises']):
                exercise_name = exercise['name'].lower()
                
                # Check if user requested a swap
                for original, requested in requested_swaps.items():
                    if original.lower() in exercise_name:
                        # Find suitable alternative
                        alternatives = substitution_rules.get(original, [])
                        
                        if requested in alternatives:
                            exercise['name'] = requested
                            exercise['notes'] = f"Swapped from {original} per user request"
                        else:
                            # Find closest match
                            best_alt = find_best_alternative(
                                original_exercise=original,
                                requested=requested,
                                available=alternatives
                            )
                            exercise['name'] = best_alt
                            exercise['notes'] = f"Alternative to {original}"
    
    new_plan['regeneration_comments'] = user_comments
    new_plan['parent_plan_id'] = original_plan['id']
    
    return new_plan

# Exercise substitution database
EXERCISE_SUBSTITUTIONS = {
    'barbell_squat': ['goblet_squat', 'front_squat', 'leg_press', 'bulgarian_split_squat'],
    'bench_press': ['dumbbell_press', 'push_ups', 'cable_press', 'machine_press'],
    'deadlift': ['romanian_deadlift', 'trap_bar_deadlift', 'rack_pulls', 'good_mornings'],
    'pull_ups': ['lat_pulldown', 'assisted_pull_ups', 'inverted_rows', 'cable_rows'],
    # ... more substitutions
}

# PDF generation structure
def generate_pdf_content(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structure plan data for PDF generation
    """
    return {
        'cover_page': {
            'title': '4-Week Personalized Training & Nutrition Plan',
            'user_name': plan['user_name'],
            'start_date': plan['start_date'],
            'goal': plan['goal'].replace('_', ' ').title()
        },
        'overview': {
            'training_days': plan['training_days'],
            'estimated_duration': plan['estimated_session_duration'],
            'equipment_needed': plan['equipment_needed'],
            'progression_strategy': plan['progression_rules']
        },
        'weekly_plans': [
            {
                'week_number': week['week_number'],
                'focus': week['focus'],
                'workouts': format_workouts_for_pdf(week['workouts'])
            }
            for week in plan['workout_weeks']
        ],
        'nutrition_plan': {
            'daily_targets': plan['diet_plan']['daily_targets'],
            'meal_schedule': plan['diet_plan']['meal_schedule'],
            'food_lists': plan['diet_plan']['food_lists'],
            'sample_meals': plan['diet_plan']['sample_meals']
        },
        'tracking_section': {
            'weight_log': generate_blank_weight_log(weeks=4),
            'measurement_log': generate_blank_measurement_log(),
            'progress_photos': generate_photo_schedule()
        }
    }