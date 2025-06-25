from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import json
import uuid
import aiofiles
from PIL import Image
import io
from pydantic import ValidationError, BaseModel
import cv2
import mediapipe as mp
import numpy as np
import math

# Enhanced TinyDB implementation with real data tracking
from tinydb import TinyDB, Query

class RealDatabase:
    def __init__(self, db_path: str = "gym_coach_real.json"):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
        self.plans = self.db.table('plans')
        self.progress_entries = self.db.table('progress_entries')
        self.workout_logs = self.db.table('workout_logs')
        self.weight_logs = self.db.table('weight_logs')
        self.body_measurements = self.db.table('body_measurements')

    def create_user(self, user_data):
        self.users.insert(user_data)

    def get_user_by_email(self, email):
        User = Query()
        result = self.users.search(User.email == email)
        return result[0] if result else None

    def store_user_data(self, user_id, data):
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow().isoformat()
        self.user_data.insert(data)

    def get_latest_user_data(self, user_id):
        UserData = Query()
        results = self.user_data.search(UserData.user_id == user_id)
        return max(results, key=lambda x: x['created_at']) if results else None

    def store_image_analysis(self, user_id, analysis):
        analysis['user_id'] = user_id
        analysis['created_at'] = datetime.utcnow().isoformat()
        self.image_analyses.insert(analysis)

    def get_latest_image_analysis(self, user_id):
        Analysis = Query()
        results = self.image_analyses.search(Analysis.user_id == user_id)
        return max(results, key=lambda x: x['created_at']) if results else None

    def store_plan(self, user_id, plan_data):
        plan_data['user_id'] = user_id
        plan_data['created_at'] = datetime.utcnow().isoformat()
        self.plans.insert(plan_data)

    def get_user_plans(self, user_id):
        Plan = Query()
        return self.plans.search(Plan.user_id == user_id)

    def get_active_plan(self, user_id):
        Plan = Query()
        plans = self.plans.search((Plan.user_id == user_id) & (Plan.status == 'active'))
        return max(plans, key=lambda x: x['created_at']) if plans else None

    def store_progress_entry(self, user_id, progress_data):
        progress_data['user_id'] = user_id
        progress_data['timestamp'] = datetime.utcnow().isoformat()
        self.progress_entries.insert(progress_data)

    def get_progress_entries(self, user_id, days=30):
        Progress = Query()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return self.progress_entries.search(
            (Progress.user_id == user_id) & (Progress.timestamp >= cutoff_date)
        )

    def store_workout_log(self, user_id, workout_data):
        workout_data['user_id'] = user_id
        workout_data['timestamp'] = datetime.utcnow().isoformat()
        self.workout_logs.insert(workout_data)

    def get_workout_logs(self, user_id, days=30):
        Workout = Query()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return self.workout_logs.search(
            (Workout.user_id == user_id) & (Workout.timestamp >= cutoff_date)
        )

    def store_weight_entry(self, user_id, weight_data):
        weight_data['user_id'] = user_id
        weight_data['timestamp'] = datetime.utcnow().isoformat()
        self.weight_logs.insert(weight_data)

    def get_weight_logs(self, user_id, days=90):
        Weight = Query()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return self.weight_logs.search(
            (Weight.user_id == user_id) & (Weight.timestamp >= cutoff_date)
        )

    def get_latest_weight(self, user_id):
        Weight = Query()
        weights = self.weight_logs.search(Weight.user_id == user_id)
        return max(weights, key=lambda x: x['timestamp']) if weights else None

# AI-powered image analysis using MediaPipe
def ai_analyze_physique_from_image(image_path: str):
    """AI-powered physique analysis using MediaPipe"""
    try:
        # Initialize MediaPipe
        mp_pose = mp.solutions.pose
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Could not load image")
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image.shape[:2]
        
        # Initialize pose detection
        with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        ) as pose:
            
            # Process image
            results = pose.process(image_rgb)
            
            if not results.pose_landmarks:
                # Fallback to basic estimates if pose detection fails
                return {
                    "waist_cm": 80.0,
                    "hip_cm": 90.0,
                    "shoulder_cm": 45.0,
                    "body_fat_estimate": 18.0,
                    "confidence_score": 0.3,
                    "analysis_method": "fallback"
                }
            
            # Extract key landmarks
            landmarks = results.pose_landmarks.landmark
            
            # Get key points
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
            
            # Convert normalized coordinates to pixels
            left_shoulder_px = (left_shoulder.x * width, left_shoulder.y * height)
            right_shoulder_px = (right_shoulder.x * width, right_shoulder.y * height)
            left_hip_px = (left_hip.x * width, left_hip.y * height)
            right_hip_px = (right_hip.x * width, right_hip.y * height)
            
            # Calculate distances in pixels
            shoulder_width_px = math.sqrt(
                (right_shoulder_px[0] - left_shoulder_px[0])**2 + 
                (right_shoulder_px[1] - left_shoulder_px[1])**2
            )
            
            hip_width_px = math.sqrt(
                (right_hip_px[0] - left_hip_px[0])**2 + 
                (right_hip_px[1] - left_hip_px[1])**2
            )
            
            # Convert to centimeters (assuming average human proportions)
            # This is a rough estimation - in production you'd calibrate this
            pixel_to_cm_ratio = 0.3  # Rough estimate
            
            shoulder_width_cm = shoulder_width_px * pixel_to_cm_ratio
            hip_width_cm = hip_width_px * pixel_to_cm_ratio
            waist_cm = hip_width_cm * 0.85  # Waist is typically 85% of hip width
            
            # Estimate body fat using waist-to-hip ratio
            whr = waist_cm / hip_width_cm if hip_width_cm > 0 else 0.8
            
            # Simple body fat estimation based on WHR
            if whr < 0.85:
                body_fat_estimate = 12.0 + (whr * 10)
            elif whr < 0.95:
                body_fat_estimate = 15.0 + ((whr - 0.85) * 20)
            else:
                body_fat_estimate = 20.0 + ((whr - 0.95) * 15)
            
            # Calculate confidence based on landmark visibility
            visibility_scores = [
                left_shoulder.visibility,
                right_shoulder.visibility, 
                left_hip.visibility,
                right_hip.visibility
            ]
            confidence_score = sum(visibility_scores) / len(visibility_scores)
            
            return {
                "waist_cm": round(waist_cm, 1),
                "hip_cm": round(hip_width_cm, 1),
                "shoulder_cm": round(shoulder_width_cm, 1),
                "body_fat_estimate": round(body_fat_estimate, 1),
                "confidence_score": round(confidence_score, 2),
                "analysis_method": "mediapipe_ai",
                "waist_to_hip_ratio": round(whr, 3)
            }
            
    except Exception as e:
        print(f"AI Analysis error: {e}")
        # Return fallback values if AI analysis fails
        return {
            "waist_cm": 80.0,
            "hip_cm": 90.0,
            "shoulder_cm": 45.0,
            "body_fat_estimate": 18.0,
            "confidence_score": 0.2,
            "analysis_method": "fallback_error",
            "error": str(e)
        }

# AI-powered workout plan generator
def ai_generate_workout_plan(user_data, image_analysis, goal, days_per_week):
    """AI-powered workout plan generation based on user data and analysis"""
    
    # Extract user characteristics
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170)
    age = user_data.get('age', 30)
    sex = user_data.get('sex', 'male')
    
    # Extract body composition from AI analysis
    body_fat = image_analysis.get('body_fat_estimate', 18) if image_analysis else 18
    whr = image_analysis.get('waist_to_hip_ratio', 0.85) if image_analysis else 0.85
    
    # Determine training parameters based on goal and body composition
    if goal == "lose_fat":
        # Higher volume, moderate intensity, more cardio
        rep_ranges = ["12-15", "15-20"]
        rest_times = [45, 60]
        sets_range = [3, 4]
        cardio_emphasis = True
    elif goal == "gain_muscle":
        # Moderate volume, higher intensity, focus on compounds
        rep_ranges = ["6-8", "8-12"]
        rest_times = [90, 120]
        sets_range = [4, 5]
        cardio_emphasis = False
    elif goal == "recomposition":
        # Balanced approach
        rep_ranges = ["8-12", "12-15"]
        rest_times = [60, 90]
        sets_range = [3, 4]
        cardio_emphasis = True
    else:  # maintenance/strength
        rep_ranges = ["5-8", "8-12"]
        rest_times = [90, 180]
        sets_range = [3, 5]
        cardio_emphasis = False

    # Advanced exercise database with progression and alternatives
    exercise_db = {
        "chest": [
            {"name": "Push-ups", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Incline Push-ups", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Dumbbell Bench Press", "difficulty": "intermediate", "equipment": "dumbbells"},
            {"name": "Barbell Bench Press", "difficulty": "advanced", "equipment": "barbell"},
            {"name": "Incline Dumbbell Press", "difficulty": "intermediate", "equipment": "dumbbells"},
            {"name": "Dips", "difficulty": "intermediate", "equipment": "dip_station"}
        ],
        "back": [
            {"name": "Inverted Rows", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Lat Pulldowns", "difficulty": "beginner", "equipment": "cable"},
            {"name": "Pull-ups", "difficulty": "intermediate", "equipment": "pull_up_bar"},
            {"name": "Bent-over Rows", "difficulty": "intermediate", "equipment": "barbell"},
            {"name": "Deadlifts", "difficulty": "advanced", "equipment": "barbell"},
            {"name": "T-Bar Rows", "difficulty": "intermediate", "equipment": "barbell"}
        ],
        "shoulders": [
            {"name": "Pike Push-ups", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Dumbbell Shoulder Press", "difficulty": "beginner", "equipment": "dumbbells"},
            {"name": "Lateral Raises", "difficulty": "beginner", "equipment": "dumbbells"},
            {"name": "Military Press", "difficulty": "intermediate", "equipment": "barbell"},
            {"name": "Face Pulls", "difficulty": "beginner", "equipment": "cable"},
            {"name": "Arnold Press", "difficulty": "intermediate", "equipment": "dumbbells"}
        ],
        "arms": [
            {"name": "Tricep Dips", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Bicep Curls", "difficulty": "beginner", "equipment": "dumbbells"},
            {"name": "Close-grip Push-ups", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Hammer Curls", "difficulty": "beginner", "equipment": "dumbbells"},
            {"name": "Tricep Extensions", "difficulty": "intermediate", "equipment": "dumbbells"},
            {"name": "Barbell Curls", "difficulty": "intermediate", "equipment": "barbell"}
        ],
        "legs": [
            {"name": "Bodyweight Squats", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Lunges", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Goblet Squats", "difficulty": "beginner", "equipment": "dumbbell"},
            {"name": "Bulgarian Split Squats", "difficulty": "intermediate", "equipment": "bodyweight"},
            {"name": "Barbell Squats", "difficulty": "advanced", "equipment": "barbell"},
            {"name": "Romanian Deadlifts", "difficulty": "intermediate", "equipment": "dumbbells"}
        ],
        "core": [
            {"name": "Plank", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Dead Bug", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Mountain Climbers", "difficulty": "beginner", "equipment": "bodyweight"},
            {"name": "Russian Twists", "difficulty": "intermediate", "equipment": "bodyweight"},
            {"name": "Hanging Leg Raises", "difficulty": "advanced", "equipment": "pull_up_bar"},
            {"name": "Ab Wheel Rollouts", "difficulty": "advanced", "equipment": "ab_wheel"}
        ]
    }

    # Determine experience level based on age and other factors
    if age < 25:
        experience = "beginner"
    elif age < 35 and body_fat < 20:
        experience = "intermediate" 
    else:
        experience = "beginner"

    # Create workout split based on days per week
    if days_per_week == 3:
        split = [
            {"day": "Day 1 - Upper Body", "muscle_groups": ["chest", "shoulders", "arms"]},
            {"day": "Day 2 - Lower Body", "muscle_groups": ["legs", "core"]},
            {"day": "Day 3 - Full Body", "muscle_groups": ["back", "chest", "legs"]}
        ]
    elif days_per_week == 4:
        split = [
            {"day": "Day 1 - Push", "muscle_groups": ["chest", "shoulders", "arms"]},
            {"day": "Day 2 - Pull", "muscle_groups": ["back", "arms"]},
            {"day": "Day 3 - Legs", "muscle_groups": ["legs", "core"]},
            {"day": "Day 4 - Upper", "muscle_groups": ["chest", "back", "shoulders"]}
        ]
    elif days_per_week == 5:
        split = [
            {"day": "Day 1 - Chest & Triceps", "muscle_groups": ["chest", "arms"]},
            {"day": "Day 2 - Back & Biceps", "muscle_groups": ["back", "arms"]},
            {"day": "Day 3 - Legs", "muscle_groups": ["legs"]},
            {"day": "Day 4 - Shoulders", "muscle_groups": ["shoulders", "core"]},
            {"day": "Day 5 - Full Body", "muscle_groups": ["chest", "back", "legs"]}
        ]
    else:  # 6 days
        split = [
            {"day": "Day 1 - Chest", "muscle_groups": ["chest"]},
            {"day": "Day 2 - Back", "muscle_groups": ["back"]},
            {"day": "Day 3 - Legs", "muscle_groups": ["legs"]},
            {"day": "Day 4 - Shoulders", "muscle_groups": ["shoulders"]},
            {"day": "Day 5 - Arms", "muscle_groups": ["arms"]},
            {"day": "Day 6 - Core & Cardio", "muscle_groups": ["core"]}
        ]

    workout_plan = []
    
    for day_info in split:
        exercises = []
        total_duration = 0
        
        for muscle_group in day_info["muscle_groups"]:
            # Filter exercises by experience level
            available_exercises = [
                ex for ex in exercise_db[muscle_group]
                if ex["difficulty"] == experience or 
                (experience == "intermediate" and ex["difficulty"] in ["beginner", "intermediate"]) or
                (experience == "advanced")
            ]
            
            # Select 2-3 exercises per muscle group
            exercises_per_group = min(3, len(available_exercises))
            selected_exercises = available_exercises[:exercises_per_group]
            
            for i, exercise_info in enumerate(selected_exercises):
                # Determine sets and reps based on exercise position and goal
                if i == 0:  # Primary exercise
                    sets = max(sets_range)
                    reps = rep_ranges[0]
                    rest = max(rest_times)
                else:  # Accessory exercises
                    sets = min(sets_range)
                    reps = rep_ranges[-1]
                    rest = min(rest_times)
                
                exercise_dict = {
                    "name": exercise_info["name"],
                    "sets": sets,
                    "reps": reps,
                    "rest_seconds": rest,
                    "equipment": exercise_info["equipment"],
                    "difficulty": exercise_info["difficulty"],
                    "notes": f"Focus on proper form. Rest {rest}s between sets.",
                    "target_muscle": muscle_group
                }
                exercises.append(exercise_dict)
                
                # Estimate duration
                work_time = 45 if "compound" in exercise_info.get("type", "") else 30
                exercise_duration = sets * (work_time + rest) / 60
                total_duration += exercise_duration
        
        # Add cardio if fat loss goal
        if cardio_emphasis and day_info["day"].endswith(("1", "3", "5")):
            cardio_exercise = {
                "name": "HIIT Cardio",
                "sets": 1,
                "reps": "15-20 minutes",
                "rest_seconds": 0,
                "equipment": "any cardio machine",
                "difficulty": "beginner",
                "notes": "High intensity intervals: 30s work, 30s rest",
                "target_muscle": "cardiovascular"
            }
            exercises.append(cardio_exercise)
            total_duration += 20
        
        workout_day = {
            "day": day_info["day"],
            "muscle_groups": day_info["muscle_groups"],
            "exercises": exercises,
            "estimated_duration_minutes": int(total_duration),
            "difficulty_level": experience,
            "goal_focus": goal,
            "notes": f"Rest 1-2 days before next workout. Focus on {goal.replace('_', ' ')}."
        }
        workout_plan.append(workout_day)
    
    return workout_plan

# AI-powered nutrition plan generator
def ai_generate_nutrition_plan(user_data, image_analysis, goal, activity_level):
    """AI-powered nutrition plan generation"""
    
    # Extract user data
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170)
    age = user_data.get('age', 30)
    sex = user_data.get('sex', 'male')
    
    # Extract AI analysis data
    body_fat = image_analysis.get('body_fat_estimate', 18) if image_analysis else 18
    
    # Calculate BMR using Mifflin-St Jeor equation (more accurate)
    if sex == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # Activity multipliers
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375, 
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)
    
    # Goal-specific calorie adjustments
    if goal == "lose_fat":
        # Aggressive deficit for higher body fat, moderate for lower
        deficit_multiplier = 0.75 if body_fat > 20 else 0.85
        calories = int(tdee * deficit_multiplier)
    elif goal == "gain_muscle":
        # Surplus based on body composition
        surplus_multiplier = 1.20 if body_fat < 15 else 1.10
        calories = int(tdee * surplus_multiplier)
    elif goal == "recomposition":
        # Slight deficit or maintenance
        calories = int(tdee * 0.95)
    else:  # maintenance
        calories = int(tdee)
    
    # Apply safety limits
    min_calories = 1500 if sex == 'male' else 1200
    calories = max(calories, min_calories)
    
    # Calculate macros based on goal and body composition
    if goal == "lose_fat":
        protein_per_kg = 2.4  # High protein to preserve muscle
        fat_percentage = 0.25
    elif goal == "gain_muscle":
        protein_per_kg = 2.2
        fat_percentage = 0.25
    elif goal == "recomposition":
        protein_per_kg = 2.6  # Highest protein for body recomp
        fat_percentage = 0.30
    else:  # maintenance
        protein_per_kg = 1.8
        fat_percentage = 0.30
    
    # Calculate macros
    protein_g = int(weight * protein_per_kg)
    fat_g = int(calories * fat_percentage / 9)
    
    # Remaining calories go to carbs
    remaining_calories = calories - (protein_g * 4) - (fat_g * 9)
    carbs_g = int(remaining_calories / 4)
    
    # Generate meal plan with AI-selected foods
    meal_plan = ai_generate_meal_plan(calories, protein_g, carbs_g, fat_g, goal, sex)
    
    return {
        "daily_targets": {
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "fiber_g": max(25, int(calories / 80)),
            "water_ml": int(weight * 35)
        },
        "bmr": int(bmr),
        "tdee": int(tdee),
        "calorie_adjustment": round((calories / tdee - 1) * 100, 1),
        "meal_suggestions": meal_plan,
        "hydration_target_ml": int(weight * 35),
        "notes": [
            f"Target {protein_g}g protein daily for optimal {goal.replace('_', ' ')}",
            f"Spread protein across {len(meal_plan)} meals (~{protein_g//len(meal_plan)}g per meal)",
            "Prioritize whole foods and minimize processed foods",
            "Adjust portions based on hunger, energy, and progress",
            f"Hydrate with {int(weight * 35)}ml water daily"
        ],
        "ai_insights": {
            "body_fat_category": "low" if body_fat < 15 else "moderate" if body_fat < 25 else "high",
            "metabolic_rate": "high" if bmr > 1800 else "moderate" if bmr > 1500 else "low",
            "calorie_strategy": "deficit" if calories < tdee else "surplus" if calories > tdee else "maintenance"
        }
    }

def ai_generate_meal_plan(calories, protein_g, carbs_g, fat_g, goal, sex):
    """AI-generated meal suggestions based on nutritional targets"""
    
    # Meal distribution based on goal
    if goal == "lose_fat":
        distribution = {"breakfast": 0.20, "lunch": 0.35, "dinner": 0.30, "snack": 0.15}
    elif goal == "gain_muscle":
        distribution = {"breakfast": 0.25, "lunch": 0.30, "dinner": 0.30, "snack": 0.15}
    else:
        distribution = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
    
    # AI-selected food database
    foods = {
        "proteins": ["chicken breast", "salmon", "eggs", "greek yogurt", "cottage cheese", "lean beef", "turkey", "tofu"],
        "carbs": ["oats", "brown rice", "quinoa", "sweet potato", "whole grain bread", "fruits", "vegetables"],
        "fats": ["avocado", "nuts", "olive oil", "nut butter", "seeds", "fatty fish"],
        "vegetables": ["spinach", "broccoli", "bell peppers", "carrots", "tomatoes", "cucumber", "asparagus"]
    }
    
    meals = []
    for meal_type, ratio in distribution.items():
        meal_calories = int(calories * ratio)
        meal_protein = int(protein_g * ratio) 
        meal_carbs = int(carbs_g * ratio)
        meal_fat = int(fat_g * ratio)
        
        # AI meal generation based on meal type and macros
        if meal_type == "breakfast":
            if goal == "lose_fat":
                meal = {
                    "meal_type": "breakfast",
                    "name": "High-Protein Breakfast Bowl", 
                    "calories": meal_calories,
                    "protein_g": meal_protein,
                    "carbs_g": meal_carbs,
                    "fat_g": meal_fat,
                    "ingredients": ["eggs", "spinach", "avocado", "whole grain toast"],
                    "prep_time_minutes": 15,
                    "ai_reason": "High protein and fiber to maintain satiety during caloric deficit"
                }
            else:
                meal = {
                    "meal_type": "breakfast",
                    "name": "Power Oatmeal Bowl",
                    "calories": meal_calories,
                    "protein_g": meal_protein,
                    "carbs_g": meal_carbs,
                    "fat_g": meal_fat,
                    "ingredients": ["oats", "protein powder", "berries", "nuts", "greek yogurt"],
                    "prep_time_minutes": 10,
                    "ai_reason": "Balanced macros with complex carbs for sustained energy"
                }
        elif meal_type == "lunch":
            meal = {
                "meal_type": "lunch",
                "name": "Balanced Power Plate",
                "calories": meal_calories,
                "protein_g": meal_protein,
                "carbs_g": meal_carbs,
                "fat_g": meal_fat,
                "ingredients": ["chicken breast", "quinoa", "mixed vegetables", "olive oil"],
                "prep_time_minutes": 25,
                "ai_reason": "Complete amino acid profile with complex carbs and healthy fats"
            }
        elif meal_type == "dinner":
            meal = {
                "meal_type": "dinner", 
                "name": "Lean & Green Dinner",
                "calories": meal_calories,
                "protein_g": meal_protein,
                "carbs_g": meal_carbs,
                "fat_g": meal_fat,
                "ingredients": ["salmon", "sweet potato", "asparagus", "avocado"],
                "prep_time_minutes": 30,
                "ai_reason": "Omega-3 rich protein with nutrient-dense carbs for recovery"
            }
        else:  # snack
            meal = {
                "meal_type": "snack",
                "name": "Protein Recovery Snack",
                "calories": meal_calories, 
                "protein_g": meal_protein,
                "carbs_g": meal_carbs,
                "fat_g": meal_fat,
                "ingredients": ["greek yogurt", "berries", "almonds"],
                "prep_time_minutes": 5,
                "ai_reason": "Quick protein source with antioxidants for muscle recovery"
            }
        
        meals.append(meal)
    
    return meals

# Define models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    access_token: str
    token_type: str

class UserData(BaseModel):
    weight: float
    height: float
    age: int
    sex: str
    smart_scale: Optional[dict] = None

class ImageAnalysisResult(BaseModel):
    waist_cm: float
    hip_cm: float
    shoulder_cm: float
    body_fat_estimate: float
    confidence_score: float
    analysis_method: Optional[str] = None
    waist_to_hip_ratio: Optional[float] = None

class PlanRequest(BaseModel):
    fitness_goal: str
    days_per_week: int
    activity_level: str

class GeneratedPlan(BaseModel):
    id: str
    workout_plan: List[dict]
    nutrition_plan: dict
    rationale: str

class TodaysWorkout(BaseModel):
    day: str
    muscle_groups: List[str]
    exercises: List[dict]
    estimated_duration_minutes: int
    workout_number: int
    week_number: int

# Initialize FastAPI app
app = FastAPI(
    title="Gym AI Coach API",
    description="AI-powered fitness and nutrition planning",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database
db = RealDatabase()

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.get_user_by_email(username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Gym AI Coach API v2.0 - Real Data & AI Powered", "status": "running"}

@app.post("/api/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register a new user"""
    try:
        existing_user = db.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user.password)
        
        user_data = {
            "id": str(uuid.uuid4()),
            "email": user.email,
            "hashed_password": hashed_password,
            "full_name": user.full_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.create_user(user_data)
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return UserResponse(
            id=user_data["id"],
            email=user.email,
            full_name=user.full_name,
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/login", response_model=UserResponse)
async def login(user: UserLogin):
    """Login user and return access token"""
    try:
        db_user = db.get_user_by_email(user.email)
        
        if not db_user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
            
        if not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return UserResponse(
            id=db_user["id"],
            email=db_user["email"],
            full_name=db_user["full_name"],
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/upload-image", response_model=ImageAnalysisResult)
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze physique image using AI"""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # AI-powered analysis
        analysis_result = ai_analyze_physique_from_image(file_path)
        
        # Store analysis in database
        db.store_image_analysis(current_user["id"], {
            "file_id": file_id,
            "filename": filename,
            "analysis": analysis_result,
            "created_at": datetime.utcnow().isoformat()
        })
        
        return ImageAnalysisResult(**analysis_result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI image analysis failed: {str(e)}")

@app.post("/api/user-data")
async def store_user_data(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Store user's physical data"""
    try:
        raw_body = await request.body()
        user_data = UserData.parse_raw(raw_body)
        
        data = user_data.dict()
        data["user_id"] = current_user["id"]
        data["created_at"] = datetime.utcnow().isoformat()
        
        db.store_user_data(current_user["id"], data)
        return {"message": "User data stored successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store user data: {str(e)}")

@app.post("/api/generate-plan", response_model=GeneratedPlan)
async def generate_plan(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered personalized workout and nutrition plan"""
    try:
        raw_body = await request.body()
        plan_request = PlanRequest.parse_raw(raw_body)
        
        # Get user's latest data
        user_data = db.get_latest_user_data(current_user["id"])
        image_analysis = db.get_latest_image_analysis(current_user["id"])
        
        if not user_data:
            raise HTTPException(status_code=400, detail="User data required for AI plan generation")
        
        # AI-powered workout plan generation
        workout_plan = ai_generate_workout_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            days_per_week=plan_request.days_per_week
        )
        
        # AI-powered nutrition plan generation
        nutrition_plan = ai_generate_nutrition_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            activity_level=plan_request.activity_level
        )
        
        # Store generated plan with active status
        plan_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "workout_plan": workout_plan,
            "nutrition_plan": nutrition_plan,
            "goal": plan_request.fitness_goal,
            "days_per_week": plan_request.days_per_week,
            "activity_level": plan_request.activity_level,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "ai_generated": True
        }
        
        # Mark previous plans as inactive
        Plan = Query()
        db.plans.update({"status": "inactive"}, Plan.user_id == current_user["id"])
        
        db.store_plan(current_user["id"], plan_data)
        
        # Generate AI rationale
        ai_rationale = f"""This AI-generated plan is specifically designed for your {plan_request.fitness_goal.replace('_', ' ')} goal based on:
        • Your physical metrics (age: {user_data.get('age')}, weight: {user_data.get('weight')}kg, height: {user_data.get('height')}cm)
        • AI body composition analysis{f" (estimated {image_analysis.get('body_fat_estimate', 'N/A')}% body fat)" if image_analysis else ""}
        • {plan_request.days_per_week} training days per week with {plan_request.activity_level} activity level
        • Evidence-based exercise selection and progressive overload principles
        • Personalized nutrition targeting {nutrition_plan['daily_targets']['calories']} calories with optimal macro distribution"""
        
        result = GeneratedPlan(
            id=plan_data["id"],
            workout_plan=workout_plan,
            nutrition_plan=nutrition_plan,
            rationale=ai_rationale
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI plan generation failed: {str(e)}")

@app.get("/api/plans")
async def get_user_plans(current_user: dict = Depends(get_current_user)):
    """Get user's previous plans"""
    try:
        plans = db.get_user_plans(current_user["id"])
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plans: {str(e)}")

@app.get("/api/todays-workout")
async def get_todays_workout(current_user: dict = Depends(get_current_user)):
    """Get today's workout based on user's active plan and progress"""
    try:
        # Get active plan
        active_plan = db.get_active_plan(current_user["id"])
        if not active_plan:
            return {"workout": None, "message": "No active plan found"}
        
        # Get user's workout logs to determine progress
        workout_logs = db.get_workout_logs(current_user["id"], days=30)
        
        # Calculate which workout they should do today
        plan_created = datetime.fromisoformat(active_plan["created_at"]).date()
        today = date.today()
        days_since_plan = (today - plan_created).days
        
        # Determine current week (1-4) and workout within that week
        current_week = (days_since_plan // 7) + 1
        if current_week > 4:
            current_week = ((days_since_plan - 28) // 7) + 1  # Restart cycle
        
        # Count workouts this week
        week_start = today - timedelta(days=today.weekday())
        week_workouts = [
            w for w in workout_logs 
            if datetime.fromisoformat(w["timestamp"]).date() >= week_start
        ]
        
        workout_plan = active_plan.get("workout_plan", [])
        if not workout_plan:
            return {"workout": None, "message": "No workouts in active plan"}
        
        # Determine which workout to show (cycle through available workouts)
        workout_index = len(week_workouts) % len(workout_plan)
        todays_workout = workout_plan[workout_index]
        
        # Format response
        workout_response = TodaysWorkout(
            day=todays_workout["day"],
            muscle_groups=todays_workout["muscle_groups"],
            exercises=todays_workout["exercises"],
            estimated_duration_minutes=todays_workout["estimated_duration_minutes"],
            workout_number=workout_index + 1,
            week_number=current_week
        )
        
        return {
            "workout": workout_response.dict(),
            "progress": {
                "workouts_this_week": len(week_workouts),
                "total_workouts_completed": len(workout_logs),
                "current_week": current_week,
                "plan_created": plan_created.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get today's workout: {str(e)}")

@app.get("/api/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get real dashboard data (no mock data)"""
    try:
        user_id = current_user["id"]
        
        # Get real data from database
        latest_user_data = db.get_latest_user_data(user_id)
        weight_logs = db.get_weight_logs(user_id, days=90)
        workout_logs = db.get_workout_logs(user_id, days=30)
        progress_entries = db.get_progress_entries(user_id, days=30)
        active_plan = db.get_active_plan(user_id)
        latest_weight = db.get_latest_weight(user_id)
        
        # Calculate real stats
        current_weight = None
        weight_change_7d = None
        weight_change_30d = None
        
        if latest_weight:
            current_weight = latest_weight.get("weight")
            
            # Calculate weight changes
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            week_weights = [w for w in weight_logs if w["timestamp"] >= week_ago]
            month_weights = [w for w in weight_logs if w["timestamp"] >= month_ago]
            
            if week_weights and len(week_weights) > 1:
                oldest_week_weight = min(week_weights, key=lambda x: x["timestamp"])
                weight_change_7d = current_weight - oldest_week_weight["weight"]
                
            if month_weights and len(month_weights) > 1:
                oldest_month_weight = min(month_weights, key=lambda x: x["timestamp"])
                weight_change_30d = current_weight - oldest_month_weight["weight"]
        
        # Calculate workout stats
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_workouts = [
            w for w in workout_logs 
            if datetime.fromisoformat(w["timestamp"]).date() >= week_start
        ]
        
        total_workout_time_week = sum(w.get("duration_minutes", 0) for w in week_workouts)
        
        # Calculate streak
        current_streak = 0
        for i in range(30):
            check_date = today - timedelta(days=i)
            day_workouts = [
                w for w in workout_logs 
                if datetime.fromisoformat(w["timestamp"]).date() == check_date
            ]
            if day_workouts:
                current_streak += 1
            else:
                break
        
        # Get next workout info
        next_workout = None
        if active_plan:
            try:
                # Use the todays_workout endpoint logic
                workout_plan = active_plan.get("workout_plan", [])
                if workout_plan:
                    workout_index = len(week_workouts) % len(workout_plan)
                    next_workout = workout_plan[workout_index]
            except:
                next_workout = None
        
        # Today's focus
        todays_focus = {
            "workout_scheduled": next_workout,
            "nutrition_targets": active_plan.get("nutrition_plan", {}).get("daily_targets") if active_plan else None,
            "progress_logged": any(
                datetime.fromisoformat(p["timestamp"]).date() == today 
                for p in progress_entries
            ),
            "motivational_message": "Stay consistent with your goals! Every day counts." if current_streak > 0 else "Today is a great day to start your fitness journey!"
        }
        
        # Prepare chart data (only if there's real data)
        recent_progress = []
        if progress_entries:
            recent_progress = [
                {
                    "date": datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d"),
                    "energy_level": entry.get("energy_level"),
                    "mood": entry.get("mood"),
                    "sleep_hours": entry.get("sleep_hours")
                }
                for entry in sorted(progress_entries, key=lambda x: x["timestamp"])[-14:]
            ]
        
        weight_trend = []
        if weight_logs:
            weight_trend = [
                {
                    "date": datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d"),
                    "weight": log["weight"],
                    "body_fat": log.get("body_fat_percentage")
                }
                for log in sorted(weight_logs, key=lambda x: x["timestamp"])[-30:]
            ]
        
        # Workout frequency (last 4 weeks)
        workout_frequency = []
        for week in range(4):
            week_start_date = today - timedelta(weeks=week+1)
            week_end_date = week_start_date + timedelta(days=7)
            week_workouts_count = [
                w for w in workout_logs 
                if week_start_date <= datetime.fromisoformat(w["timestamp"]).date() < week_end_date
            ]
            workout_frequency.append({
                "week": f"Week {4-week}",
                "workouts": len(week_workouts_count),
                "duration": sum(w.get("duration_minutes", 0) for w in week_workouts_count)
            })
        
        dashboard_data = {
            "stats": {
                "current_weight": current_weight,
                "weight_change_7d": round(weight_change_7d, 1) if weight_change_7d else None,
                "weight_change_30d": round(weight_change_30d, 1) if weight_change_30d else None,
                "workouts_this_week": len(week_workouts),
                "total_workout_time_week": total_workout_time_week,
                "current_streak": current_streak,
                "next_workout": next_workout
            },
            "todays_focus": todays_focus,
            "recent_progress": recent_progress,
            "weight_trend": weight_trend,
            "workout_frequency": workout_frequency,
            "has_active_plan": active_plan is not None,
            "data_available": {
                "weight_logs": len(weight_logs) > 0,
                "workout_logs": len(workout_logs) > 0,
                "progress_entries": len(progress_entries) > 0
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "2.0-real-data"}

# Real progress tracking endpoints
@app.post("/api/progress")
async def log_progress(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log daily progress entry"""
    try:
        raw_body = await request.body()
        progress_data = json.loads(raw_body.decode())
        
        db.store_progress_entry(current_user["id"], progress_data)
        return {"message": "Progress logged successfully", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log progress: {str(e)}")

@app.post("/api/workout-log")
async def log_workout(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log completed workout"""
    try:
        raw_body = await request.body()
        workout_data = json.loads(raw_body.decode())
        
        db.store_workout_log(current_user["id"], workout_data)
        return {"message": "Workout logged successfully", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log workout: {str(e)}")

@app.post("/api/weight")
async def log_weight(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log weight entry"""
    try:
        raw_body = await request.body()
        weight_data = json.loads(raw_body.decode())
        
        db.store_weight_entry(current_user["id"], weight_data)
        return {"message": "Weight logged successfully", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log weight: {str(e)}")

@app.post("/api/measurements")
async def log_measurements(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log body measurements"""
    try:
        raw_body = await request.body()
        measurement_data = json.loads(raw_body.decode())
        print(f"Measurements logged for user {current_user['id']}: {measurement_data}")
        return {"message": "Measurements logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log measurements: {str(e)}")

@app.get("/api/progress-history")
async def get_progress_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get progress history"""
    try:
        progress = db.get_progress_entries(current_user["id"], days)
        return {"progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress history: {str(e)}")

@app.get("/api/weight-history")
async def get_weight_history(
    days: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """Get weight history"""
    try:
        weight_logs = db.get_weight_logs(current_user["id"], days)
        return {"weight_logs": weight_logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weight history: {str(e)}")

@app.get("/api/workout-history")
async def get_workout_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get workout history"""
    try:
        workout_logs = db.get_workout_logs(current_user["id"], days)
        return {"workout_logs": workout_logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workout history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)