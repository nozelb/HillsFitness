from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    access_token: str
    token_type: str

class SmartScaleData(BaseModel):
    body_fat_percentage: Optional[float] = None
    muscle_percentage: Optional[float] = None
    visceral_fat: Optional[float] = None

class UserData(BaseModel):
    weight: float  # kg
    height: float  # cm
    age: int
    sex: str  # "male" or "female"
    smart_scale: Optional[SmartScaleData] = None

class ImageAnalysisResult(BaseModel):
    waist_cm: float
    hip_cm: Optional[float] = None
    shoulder_cm: float
    body_fat_estimate: float
    confidence_score: float

class PlanRequest(BaseModel):
    fitness_goal: str  # "lose_fat", "gain_muscle", "recomposition", "maintenance"
    days_per_week: int = 4
    activity_level: str = "moderate"  # "sedentary", "light", "moderate", "active", "very_active"

class Exercise(BaseModel):
    name: str
    sets: int
    reps: str  # Can be range like "8-12"
    rest_seconds: int
    notes: Optional[str] = None

class WorkoutDay(BaseModel):
    day: str
    muscle_groups: List[str]
    exercises: List[Exercise]
    estimated_duration_minutes: int

class NutritionTarget(BaseModel):
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int

class MealSuggestion(BaseModel):
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    name: str
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    ingredients: List[str]

class GeneratedPlan(BaseModel):
    id: str
    workout_plan: List[Dict[str, Any]]  # Changed to Dict for serialization
    nutrition_plan: Dict[str, Any]
    rationale: str

# NEW: Progress tracking models
class ProgressEntry(BaseModel):
    date: str  # YYYY-MM-DD format
    weight: Optional[float] = None
    energy_level: Optional[int] = None  # 1-10 scale
    mood: Optional[int] = None  # 1-10 scale
    sleep_hours: Optional[float] = None
    water_intake_liters: Optional[float] = None
    notes: Optional[str] = None

class WorkoutLog(BaseModel):
    workout_name: str
    duration_minutes: int
    exercises_completed: List[Dict[str, Any]]  # List of completed exercises with actual reps/sets
    difficulty_rating: Optional[int] = None  # 1-10 scale
    notes: Optional[str] = None

class WeightEntry(BaseModel):
    weight: float  # kg
    body_fat_percentage: Optional[float] = None
    muscle_percentage: Optional[float] = None
    notes: Optional[str] = None

class BodyMeasurements(BaseModel):
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    bicep_cm: Optional[float] = None
    thigh_cm: Optional[float] = None
    notes: Optional[str] = None

# Dashboard response models
class DashboardStats(BaseModel):
    current_weight: Optional[float] = None
    weight_change_7d: Optional[float] = None
    weight_change_30d: Optional[float] = None
    workouts_this_week: int
    total_workout_time_week: int  # minutes
    current_streak: int  # days
    next_workout: Optional[Dict[str, Any]] = None

class TodaysFocus(BaseModel):
    workout_scheduled: Optional[Dict[str, Any]] = None
    nutrition_targets: Optional[Dict[str, Any]] = None
    progress_logged: bool
    motivational_message: str

class DashboardResponse(BaseModel):
    stats: DashboardStats
    todays_focus: TodaysFocus
    recent_progress: List[Dict[str, Any]]
    weight_trend: List[Dict[str, Any]]
    workout_frequency: List[Dict[str, Any]]