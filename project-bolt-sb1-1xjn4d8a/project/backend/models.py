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
    workout_plan: List[WorkoutDay]
    nutrition_plan: Dict[str, Any]  # Contains targets and meal suggestions
    rationale: str