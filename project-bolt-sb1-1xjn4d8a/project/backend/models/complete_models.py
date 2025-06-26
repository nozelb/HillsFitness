# backend/models/complete_models.py
"""
Complete data models exactly matching the specification
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums for strict validation
class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"

class PrimaryGoal(str, Enum):
    MUSCLE_GAIN = "muscle-gain"
    FAT_LOSS = "fat-loss"
    RECOMP = "recomp"
    MAINTENANCE = "maintenance"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    HIGH = "high"

# STATIC PROFILE (persisted once, editable on profile page)
class StaticProfile(BaseModel):
    """Static user profile - collected once and persisted"""
    fullName: str = Field(..., min_length=1, max_length=100)
    dob: date = Field(..., description="Date of birth in ISO format")
    sex: Sex
    primaryGoal: PrimaryGoal
    trainDays: int = Field(..., ge=1, le=7, description="Training days per week")
    activityLvl: ActivityLevel

    @validator('dob')
    def validate_dob(cls, v):
        """Ensure user is at least 13 years old"""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13:
            raise ValueError("User must be at least 13 years old")
        if age > 100:
            raise ValueError("Invalid date of birth")
        return v

    @property
    def age(self) -> int:
        """Calculate current age"""
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

# DYNAMIC WIZARD DATA (collected each time a plan is generated)
class SmartScaleData(BaseModel):
    """Smart scale measurements - may be null if unavailable"""
    bodyFatPct: Optional[float] = Field(None, ge=3.0, le=60.0)
    musclePct: Optional[float] = Field(None, ge=20.0, le=70.0)
    visceralFatScore: Optional[int] = Field(None, ge=1, le=30)

class WizardInputs(BaseModel):
    """Dynamic data collected for each plan generation"""
    photoUrl: str = Field(..., description="URL to uploaded photo")
    heightCm: float = Field(..., ge=100, le=230, description="Height in centimeters")
    weightKg: float = Field(..., ge=30, le=300, description="Weight in kilograms")
    smartScale: Optional[SmartScaleData] = None
    injuries: List[str] = Field(default_factory=list, description="List of current injuries")
    equipLimits: List[str] = Field(default_factory=list, description="Equipment limitations")
    userComment: Optional[str] = Field(None, max_length=500, description="Additional user notes")

# VISION ANALYSIS RESULT (from image analysis micro-service)
class AnthropometricMeasurements(BaseModel):
    """Body measurements from vision analysis"""
    waistCm: float = Field(..., ge=50, le=200)
    hipCm: float = Field(..., ge=60, le=200)
    shoulderCm: float = Field(..., ge=30, le=80)

class VisionAnalysisResult(BaseModel):
    """Result from vision analysis microservice"""
    quality: float = Field(..., ge=0.0, le=1.0, description="Image quality score 0-1")
    bfEstimate: float = Field(..., ge=3.0, le=60.0, description="Body fat percentage estimate")
    anthro: AnthropometricMeasurements
    poseAlerts: List[str] = Field(default_factory=list, description="Posture issues detected")

    @validator('quality')
    def validate_quality(cls, v):
        """Abort plan generation if quality < 0.70"""
        if v < 0.70:
            raise ValueError("Image quality too low - please upload a clearer photo")
        return v

# COMPLETE DATA CONTRACT (what the LLM receives)
class CompleteDataContract(BaseModel):
    """Complete data contract passed to plan generation"""
    profile: StaticProfile
    wizard: WizardInputs
    vision: VisionAnalysisResult

# PLAN GENERATION MODELS
class Exercise(BaseModel):
    """Individual exercise in workout plan"""
    name: str
    sets: int = Field(..., ge=1, le=10)
    reps: str = Field(..., description="Rep range e.g. '8-12' or '30 seconds'")
    rest: str = Field(..., description="Rest period e.g. '90 s' or '2 min'")
    muscle_groups: List[str] = Field(default_factory=list)
    equipment: Optional[str] = None
    notes: Optional[str] = None
    corrective: bool = Field(default=False, description="Is this a corrective exercise")

class WorkoutDay(BaseModel):
    """Single day of workout plan"""
    day: str = Field(..., description="e.g. 'Day 1' or 'Monday'")
    exercises: List[Exercise]
    estimated_duration_minutes: int = Field(..., ge=15, le=120)
    focus: List[str] = Field(default_factory=list, description="Primary muscle groups")

class WeeklyWorkout(BaseModel):
    """4-week workout mesocycle"""
    week: int = Field(..., ge=1, le=4)
    days: List[WorkoutDay]
    progression_notes: Optional[str] = None

class NutritionTargets(BaseModel):
    """Weekly nutrition targets in metric units"""
    week: int = Field(..., ge=1, le=4)
    kJ_per_day: int = Field(..., ge=4000, le=20000, description="Kilojoules per day")
    protein_g: float = Field(..., ge=50, le=300)
    carbs_g: float = Field(..., ge=50, le=800)
    fat_g: float = Field(..., ge=30, le=200)

class MealIdea(BaseModel):
    """Sample meal with metric measurements"""
    name: str
    kJ: int = Field(..., description="Kilojoules")
    protein_g: float
    carbs_g: float
    fat_g: float
    ingredients: List[str]
    weight_g: Dict[str, float] = Field(default_factory=dict, description="Ingredient weights in grams")
    prep_time_minutes: int = Field(..., ge=1, le=120)

class MobilityDrill(BaseModel):
    """Corrective mobility exercise"""
    name: str
    sets: int
    reps: str
    frequency: str = Field(..., description="e.g. 'daily', '3x per week'")
    target_issue: str = Field(..., description="What this addresses")
    instructions: List[str] = Field(default_factory=list)

class PlanRationale(BaseModel):
    """Why we chose this approach"""
    bullet_points: List[str] = Field(..., min_items=1, max_items=5)
    references_user_data: bool = Field(default=True, description="Does rationale reference user data")

class CompletePlan(BaseModel):
    """Complete 4-week fitness plan"""
    plan_id: str
    user_id: str
    created_at: datetime
    
    # Core plan components
    weekly_nutrition: List[NutritionTargets]
    workout_mesocycle: List[WeeklyWorkout]
    meal_ideas: List[MealIdea]
    mobility_drills: List[MobilityDrill]
    rationale: PlanRationale
    
    # Plan metadata
    duration_weeks: int = Field(default=4, ge=1, le=12)
    difficulty_level: str = Field(..., description="beginner/intermediate/advanced")
    equipment_required: List[str] = Field(default_factory=list)
    
    # Legal disclaimer
    disclaimer: str = Field(
        default="Information is for educational purposes only and is not a substitute for professional medical advice. Consult a healthcare provider before starting any exercise or nutrition program."
    )

# API RESPONSE MODELS (exactly matching specification format)
class PlanOverview(BaseModel):
    """Overview section of plan response"""
    summary: str
    duration_weeks: int
    training_days_per_week: int
    estimated_time_per_session: str
    disclaimer: str

class WeeklyNutritionTable(BaseModel):
    """Nutrition table exactly as specified"""
    week: str  # "1-4" format
    kJ_per_day: int
    protein_g: int
    carbs_g: int
    fat_g: int

class TrainingTable(BaseModel):
    """Training table exactly as specified"""
    day: str
    exercise: str
    sets: int
    reps: str
    rest: str

class FormattedPlanResponse(BaseModel):
    """Final formatted response matching specification exactly"""
    overview: PlanOverview
    weekly_nutrition_targets: List[WeeklyNutritionTable]
    training_mesocycle: List[TrainingTable]
    meal_ideas: List[str]  # Simplified meal descriptions
    mobility_posture_drills: List[str]  # Simplified drill descriptions
    rationale: List[str]  # Bullet points as specified
    
    # Action buttons (handled by frontend)
    actions: List[str] = Field(
        default=["Download PDF", "Accept Plan", "Regenerate"],
        description="Available user actions"
    )

# VALIDATION AND SAFETY MODELS
class ValidationError(BaseModel):
    """Input validation error"""
    field: str
    message: str
    code: str

class SafetyCheck(BaseModel):
    """Safety validation results"""
    is_safe: bool
    warnings: List[str] = Field(default_factory=list)
    blocked_exercises: List[str] = Field(default_factory=list)
    calorie_adjustments: Optional[str] = None

# PROGRESS TRACKING MODELS (for after plan acceptance)
class SessionLog(BaseModel):
    """Individual workout session log"""
    session_id: str
    plan_id: str
    user_id: str
    date: date
    exercises_completed: List[str]
    exercises_skipped: List[str]
    duration_minutes: int
    difficulty_rating: int = Field(..., ge=1, le=10)
    notes: Optional[str] = None

class ProgressMetrics(BaseModel):
    """Progress tracking metrics"""
    sessions_completed: int
    sessions_scheduled: int
    compliance_percentage: float
    avg_session_duration: float
    missed_sessions_last_7_days: int

# REGENERATION MODELS
class RegenerationRequest(BaseModel):
    """Request to modify existing plan"""
    plan_id: str
    user_comment: str = Field(..., max_length=500, description="What to change")
    preserve_difficulty: bool = Field(default=True)
    preserve_muscle_emphasis: bool = Field(default=True)

class RegenerationResponse(BaseModel):
    """Response to regeneration request"""
    success: bool
    new_plan_id: Optional[str] = None
    changes_made: List[str] = Field(default_factory=list)
    queued_for_email: bool = Field(default=False, description="If exceeded free regenerations")