from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from pydantic import EmailStr

class FitnessGoal(str, Enum):
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    RECOMPOSITION = "recomposition"
    MAINTENANCE = "maintenance"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    HIGH = "high"
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

# Enhanced User Profile (static data)
class UserProfile(BaseModel):
    user_id: str
    date_of_birth: date
    full_name: str
    gender: Gender
    primary_fitness_goal: FitnessGoal
    preferred_training_days: int  # 3-6 days
    activity_level: ActivityLevel
    
    @validator('preferred_training_days')
    def validate_training_days(cls, v):
        if not 3 <= v <= 6:
            raise ValueError('Training days must be between 3 and 6')
        return v
    
    @property
    def age(self) -> int:
        """Auto-calculate age from date of birth"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

# Enhanced Plan Generation Request
class EnhancedPlanRequest(BaseModel):
    height: float  # cm - editable for growing users
    weight: float  # kg - pre-filled from last entry
    body_fat_percentage: Optional[float] = None
    muscle_percentage: Optional[float] = None
    visceral_fat: Optional[float] = None
    bone_mass: Optional[float] = None
    water_percentage: Optional[float] = None
    metabolic_age: Optional[int] = None
    photo_id: str  # Reference to uploaded full-body photo
    
class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    REGENERATED = "regenerated"

# Enhanced Plan with 4-week structure
class EnhancedPlan(BaseModel):
    id: str
    user_id: str
    status: PlanStatus
    created_at: datetime
    accepted_at: Optional[datetime] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # 4-week workout structure
    workout_weeks: List[Dict[str, Any]]  # 4 weeks of workouts
    
    # Matching diet plan
    diet_plan: Dict[str, Any]
    
    # Progression rules
    progression_rules: Dict[str, Any]
    
    # User feedback for regeneration
    regeneration_comments: Optional[str] = None
    parent_plan_id: Optional[str] = None  # Links to previous plan if regenerated

# Plan acceptance tracking
class PlanAcceptance(BaseModel):
    plan_id: str
    user_id: str
    accepted_at: datetime
    scheduled_completion: date  # 4 weeks from acceptance
    
# Workout session tracking
class WorkoutSession(BaseModel):
    id: str
    user_id: str
    plan_id: str
    week_number: int  # 1-4
    day_number: int  # 1-7
    scheduled_date: date
    completed_at: Optional[datetime] = None
    exercises_completed: List[Dict[str, Any]]
    notes: Optional[str] = None
    
# Progress tracking with photos
class ProgressPhoto(BaseModel):
    id: str
    user_id: str
    photo_url: str
    taken_at: datetime
    weight: float
    body_fat_percentage: Optional[float] = None
    notes: Optional[str] = None

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
    fitness_goal: str  # "fat_loss", "muscle_gain", "recomposition", "maintenance"
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