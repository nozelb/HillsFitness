import re
import math
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Calculate Basal Metabolic Rate using Harris-Benedict equation"""
    if sex.lower() == "male":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return bmr

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure"""
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "athlete": 1.9
    }
    return bmr * activity_multipliers.get(activity_level.lower(), 1.55)

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def classify_bmi(bmi: float) -> str:
    """Classify BMI into categories"""
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"

def estimate_body_fat_navy(waist_cm: float, neck_cm: float, height_cm: float, 
                          sex: str, hip_cm: Optional[float] = None) -> float:
    """Estimate body fat using US Navy method"""
    try:
        if sex.lower() == "male":
            if waist_cm <= neck_cm or height_cm <= 0:
                return 15.0  # Default estimate
            body_fat = 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
        else:
            if not hip_cm or waist_cm + hip_cm <= neck_cm or height_cm <= 0:
                return 22.0  # Default estimate
            body_fat = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 78.387
        
        return max(5.0, min(50.0, body_fat))
    except (ValueError, ZeroDivisionError):
        return 20.0 if sex.lower() == "female" else 15.0

def parse_feedback(feedback: str) -> Dict[str, Any]:
    """Parse user feedback for plan modifications"""
    modifications = {}
    feedback_lower = feedback.lower()
    
    # Exercise replacements
    replace_patterns = [
        r"replace (\w+) with (\w+)",
        r"substitute (\w+) for (\w+)",
        r"swap (\w+) with (\w+)"
    ]
    
    replacements = {}
    for pattern in replace_patterns:
        matches = re.findall(pattern, feedback_lower)
        for match in matches:
            replacements[match[0]] = match[1]
    
    if replacements:
        modifications["replace_exercises"] = replacements
    
    # Time reductions
    time_patterns = [
        r"reduce.*time.*(\d+).*minutes?",
        r"shorter.*workouts?.*(\d+).*minutes?",
        r"(\d+).*minutes?.*maximum"
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, feedback_lower)
        if match:
            modifications["reduce_time"] = int(match.group(1))
            break
    
    # Nutrition changes
    nutrition_keywords = ["calories", "protein", "carbs", "fat", "diet", "nutrition"]
    if any(keyword in feedback_lower for keyword in nutrition_keywords):
        modifications["change_nutrition"] = feedback
    
    return modifications

def validate_measurements(measurements: Dict[str, Any]) -> List[str]:
    """Validate measurement inputs and return list of errors"""
    errors = []
    
    # Height validation
    height = measurements.get("height_cm")
    if height and (height < 100 or height > 250):
        errors.append("Height must be between 100-250 cm")
    
    # Weight validation
    weight = measurements.get("weight_kg")
    if weight and (weight < 30 or weight > 300):
        errors.append("Weight must be between 30-300 kg")
    
    # Body fat validation
    body_fat = measurements.get("body_fat_percentage")
    if body_fat and (body_fat < 3 or body_fat > 50):
        errors.append("Body fat percentage must be between 3-50%")
    
    # Muscle mass validation
    muscle_mass = measurements.get("muscle_mass_percentage")
    if muscle_mass and (muscle_mass < 20 or muscle_mass > 60):
        errors.append("Muscle mass percentage must be between 20-60%")
    
    return errors

def calculate_age(date_of_birth: date) -> int:
    """Calculate age from date of birth"""
    today = date.today()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def format_exercise_name(name: str) -> str:
    """Format exercise name for display"""
    return name.replace("_", " ").title()

def calculate_plan_completion_percentage(plan_start: date, plan_duration_weeks: int = 4) -> float:
    """Calculate how much of the plan has been completed"""
    today = date.today()
    plan_end = plan_start + timedelta(weeks=plan_duration_weeks)
    
    if today < plan_start:
        return 0.0
    elif today > plan_end:
        return 100.0
    else:
        days_total = (plan_end - plan_start).days
        days_completed = (today - plan_start).days
        return (days_completed / days_total) * 100

def generate_motivational_message(progress_data: Dict[str, Any]) -> str:
    """Generate personalized motivational message based on progress"""
    completion = progress_data.get("completion_percentage", 0)
    workouts_completed = progress_data.get("workouts_completed", 0)
    
    if completion < 25:
        messages = [
            "Great start! You're building the foundation for success.",
            "Every journey begins with a single step. Keep going!",
            "Consistency is key. You're on the right track!"
        ]
    elif completion < 50:
        messages = [
            "You're making excellent progress! Keep up the momentum.",
            "Halfway there! Your dedication is paying off.",
            "Strong work! Your body is adapting and getting stronger."
        ]
    elif completion < 75:
        messages = [
            "You're in the home stretch! Don't stop now.",
            "Amazing progress! Your hard work is really showing.",
            "You're crushing it! The finish line is in sight."
        ]
    else:
        messages = [
            "Incredible! You're almost at the finish line.",
            "Outstanding commitment! You should be proud of your progress.",
            "You're a fitness champion! Time to plan your next challenge."
        ]
    
    return messages[workouts_completed % len(messages)]

def calculate_next_plan_suggestions(current_plan: Dict[str, Any], progress: Dict[str, Any]) -> List[str]:
    """Suggest focus areas for the next plan based on current progress"""
    suggestions = []
    
    goal = current_plan.get("goal", "")
    completion_rate = progress.get("workout_completion_rate", 0)
    
    if completion_rate > 80:
        suggestions.append("Consider increasing training intensity or frequency")
        if goal == "lose_fat":
            suggestions.append("Add more cardio or HIIT sessions")
        elif goal == "gain_muscle":
            suggestions.append("Focus on progressive overload with heavier weights")
    elif completion_rate < 60:
        suggestions.append("Focus on consistency and building the habit first")
        suggestions.append("Consider reducing workout frequency to ensure sustainability")
    
    # Goal-specific suggestions
    if goal == "lose_fat":
        suggestions.extend([
            "Target different muscle groups for variety",
            "Include strength training to preserve muscle mass",
            "Consider incorporating more compound movements"
        ])
    elif goal == "gain_muscle":
        suggestions.extend([
            "Increase training volume for lagging muscle groups",
            "Focus on progressive overload principles",
            "Consider specialization phases for specific muscles"
        ])
    
    return suggestions[:3]  # Return top 3 suggestions

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human-readable string"""
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours > 1 else ''} {remaining_minutes} minutes"

def validate_profile_data(profile_data: Dict[str, Any]) -> List[str]:
    """Validate profile data and return list of errors"""
    errors = []
    required_fields = ["full_name", "date_of_birth", "sex", "primary_fitness_goal"]
    
    for field in required_fields:
        if not profile_data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate date of birth
    dob = profile_data.get("date_of_birth")
    if dob:
        try:
            if isinstance(dob, str):
                dob = datetime.strptime(dob, "%Y-%m-%d").date()
            age = calculate_age(dob)
            if age < 13 or age > 100:
                errors.append("Age must be between 13 and 100 years")
        except (ValueError, TypeError):
            errors.append("Invalid date of birth format")
    
    # Validate training days
    training_days = profile_data.get("preferred_training_days")
    if training_days and (training_days < 3 or training_days > 6):
        errors.append("Training days must be between 3 and 6")
    
    return errors
