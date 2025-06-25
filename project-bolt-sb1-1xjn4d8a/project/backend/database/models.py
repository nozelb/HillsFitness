# backend/database/models.py - Enhanced Pydantic models

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"

class FitnessGoal(str, Enum):
    LOSE_FAT = "lose_fat"
    GAIN_MUSCLE = "gain_muscle"
    STRENGTH = "strength"
    RECOMPOSITION = "recomposition"
    MAINTENANCE = "maintenance"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"      # Little to no exercise
    LIGHT = "light"              # Light exercise 1-3 days/week
    MODERATE = "moderate"        # Moderate exercise 3-5 days/week
    ACTIVE = "active"            # Heavy exercise 6-7 days/week
    ATHLETE = "athlete"          # Very heavy exercise, physical job

class GymExperience(str, Enum):
    BEGINNER = "beginner"        # 0-6 months
    INTERMEDIATE = "intermediate" # 6 months - 2 years
    ADVANCED = "advanced"        # 2+ years

class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    REGENERATED = "regenerated"

# Authentication Models
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

# User Data Models
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

# Plan Generation Models
class PlanRequest(BaseModel):
    fitness_goal: str
    days_per_week: int
    activity_level: str

class Exercise(BaseModel):
    name: str
    sets: int
    reps: str


# Core User Models
class UserProfile(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    sex: Sex
    primary_fitness_goal: FitnessGoal
    preferred_training_days: int = Field(ge=3, le=6, description="Training days per week (3-6)")
    activity_level: ActivityLevel
    gym_experience: GymExperience = GymExperience.BEGINNER
    
    # Preferences
    dietary_restrictions: Optional[List[str]] = []
    equipment_available: Optional[List[str]] = ["basic_gym"]  # basic_gym, home, full_gym
    injury_history: Optional[List[str]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('preferred_training_days')
    def validate_training_days(cls, v):
        if not 3 <= v <= 6:
            raise ValueError('Training days must be between 3 and 6')
        return v
    
    @property
    def age(self) -> int:
        """Calculate current age from date of birth"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

class UserMeasurements(BaseModel):
    user_id: str
    version: int = 1
    
    # Basic measurements
    height_cm: float = Field(gt=100, lt=250, description="Height in centimeters")
    weight_kg: float = Field(gt=30, lt=300, description="Weight in kilograms")
    
    # Smart scale data (optional)
    body_fat_percentage: Optional[float] = Field(None, ge=5, le=50)
    muscle_mass_percentage: Optional[float] = Field(None, ge=20, le=60)
    visceral_fat: Optional[float] = Field(None, ge=1, le=30)
    water_percentage: Optional[float] = Field(None, ge=30, le=80)
    bone_mass_kg: Optional[float] = Field(None, ge=1, le=10)
    metabolic_age: Optional[int] = Field(None, ge=10, le=100)
    
    # Image analysis results
    image_analysis: Optional[Dict[str, Any]] = None
    photo_id: Optional[str] = None
    
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

# Exercise and Workout Models
class Exercise(BaseModel):
    name: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty: str  # beginner, intermediate, advanced
    sets: int = Field(ge=1, le=10)
    reps: str  # e.g., "8-12", "12-15", "AMRAP"
    rest_seconds: int = Field(ge=30, le=300)
    weight_progression: Optional[str] = None  # e.g., "+2.5kg", "+5%"
    notes: Optional[str] = None
    substitutions: Optional[List[str]] = []  # Alternative exercises
    safety_notes: Optional[str] = None

class WorkoutDay(BaseModel):
    day_number: int = Field(ge=1, le=7)
    day_name: str  # e.g., "Push Day", "Pull Day", "Legs"
    muscle_groups: List[str]
    exercises: List[Exercise] = Field(min_items=5, description="Minimum 5 exercises per day")
    estimated_duration_minutes: int = Field(ge=30, le=120)
    difficulty_rating: int = Field(ge=1, le=10, description="Overall workout difficulty")
    
    @validator('exercises')
    def validate_minimum_exercises(cls, v):
        if len(v) < 5:
            raise ValueError('Each workout day must have at least 5 exercises')
        return v

class WorkoutWeek(BaseModel):
    week_number: int = Field(ge=1, le=4)
    focus: str  # e.g., "Foundation", "Intensity", "Peak", "Deload"
    workouts: List[WorkoutDay]
    volume_multiplier: float = Field(ge=0.5, le=1.5, description="Progressive overload multiplier")
    notes: Optional[str] = None

# Nutrition Models
class NutritionTargets(BaseModel):
    calories: int = Field(ge=1200, le=5000, description="Daily calorie target")
    protein_g: int = Field(ge=50, le=300)
    carbs_g: int = Field(ge=50, le=500)
    fat_g: int = Field(ge=30, le=200)
    fiber_g: int = Field(ge=20, le=60)
    water_ml: int = Field(ge=1500, le=5000)
    
    # Micronutrient goals (optional)
    sodium_mg: Optional[int] = Field(None, le=2300)
    calcium_mg: Optional[int] = Field(None, ge=1000)
    iron_mg: Optional[int] = Field(None, ge=8)

class Meal(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    name: str
    description: Optional[str] = None
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    prep_time_minutes: Optional[int] = None
    ingredients: List[str]
    instructions: Optional[List[str]] = []
    dietary_tags: Optional[List[str]] = []  # vegetarian, vegan, gluten-free, etc.

class NutritionPlan(BaseModel):
    daily_targets: NutritionTargets
    bmr: int
    tdee: int
    calorie_adjustment: float  # Surplus/deficit percentage
    meal_plan: List[Meal]
    hydration_schedule: List[str]  # Hydration reminders throughout day
    supplement_recommendations: Optional[List[str]] = []
    
    # Safety checks
    deficit_within_limits: bool = True
    minimum_calories_met: bool = True
    protein_adequate: bool = True
    
    # Tips and guidelines
    nutrition_tips: List[str]
    meal_timing_advice: List[str]
    dos_and_donts: Dict[str, List[str]]

# Complete Plan Model
class CompletePlan(BaseModel):
    id: str
    user_id: str
    version: int = 1
    status: PlanStatus = PlanStatus.DRAFT
    
    # Plan hierarchy
    parent_plan_id: Optional[str] = None  # For regenerated plans
    regeneration_reason: Optional[str] = None
    
    # 4-week structure
    workout_weeks: List[WorkoutWeek] = Field(min_items=4, max_items=4)
    nutrition_plan: NutritionPlan
    
    # User preferences applied
    profile_snapshot: UserProfile  # Snapshot of profile when plan was created
    measurements_snapshot: UserMeasurements
    
    # Safety and compliance
    safety_checks: Dict[str, bool] = {}
    warning_messages: Optional[List[str]] = []
    
    # User feedback and interaction
    user_feedback: Optional[str] = None
    approved_by_user: bool = False
    plan_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Plan statistics
    total_workouts: int = Field(ge=12, le=24, description="Total workouts in 4 weeks")
    estimated_time_per_week: int = Field(description="Minutes per week")

# Progress Tracking Models
class ProgressEntry(BaseModel):
    user_id: str
    
    # Physical measurements
    weight_kg: Optional[float] = Field(None, gt=30, lt=300)
    body_fat_percentage: Optional[float] = Field(None, ge=5, le=50)
    muscle_mass_kg: Optional[float] = Field(None, gt=10, lt=100)
    
    # Body measurements (cm)
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    bicep_cm: Optional[float] = None
    thigh_cm: Optional[float] = None
    
    # Wellness metrics
    energy_level: Optional[int] = Field(None, ge=1, le=10, description="Energy level (1-10)")
    mood_rating: Optional[int] = Field(None, ge=1, le=10, description="Mood (1-10)")
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    
    # Performance metrics
    workouts_completed_week: Optional[int] = Field(None, ge=0, le=7)
    nutrition_adherence: Optional[int] = Field(None, ge=1, le=10, description="Diet adherence (1-10)")
    
    # Photos and notes
    progress_photo_id: Optional[str] = None
    notes: Optional[str] = None
    achievements: Optional[List[str]] = []
    challenges: Optional[List[str]] = []
    
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

# Check-in and Notification Models
class CheckInType(str, Enum):
    WEEKLY_WEIGHT = "weekly_weight"
    PROGRESS_PHOTO = "progress_photo"
    PLAN_FEEDBACK = "plan_feedback"
    WELLNESS_CHECK = "wellness_check"
    PLAN_COMPLETION = "plan_completion"

class CheckIn(BaseModel):
    user_id: str
    type: CheckInType
    title: str
    description: str
    due_date: date
    reminder_sent: bool = False
    completed_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, completed, skipped, overdue
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Plan Generation Request Models
class PlanGenerationRequest(BaseModel):
    """Request for generating a new plan - only dynamic data needed"""
    measurements: UserMeasurements
    specific_goals: Optional[List[str]] = []  # Additional goals for this plan
    exercise_preferences: Optional[Dict[str, Any]] = {}
    equipment_limitations: Optional[List[str]] = []
    time_constraints: Optional[Dict[str, int]] = {}  # max_workout_time, available_days
    
class PlanRegenerationRequest(BaseModel):
    """Request for regenerating an existing plan with modifications"""
    original_plan_id: str
    feedback: str  # "replace squats with lunges", "reduce workout time", etc.
    specific_changes: Optional[Dict[str, Any]] = {}

# API Response Models
class PlanSummary(BaseModel):
    id: str
    version: int
    status: PlanStatus
    created_at: datetime
    total_workouts: int
    estimated_duration_weeks: int = 4
    goal: FitnessGoal
    completion_percentage: Optional[float] = None

class DashboardData(BaseModel):
    current_plan: Optional[PlanSummary] = None
    recent_progress: List[ProgressEntry]
    upcoming_checkins: List[CheckIn]
    weekly_stats: Dict[str, Any]
    progress_charts: Dict[str, List[Dict[str, Any]]]
    motivational_message: str
    next_workout: Optional[WorkoutDay] = None