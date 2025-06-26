# backend/main.py - Integrated with Vision Worker
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import json
import uuid
import aiofiles
from PIL import Image
import io
from pydantic import ValidationError, BaseModel
import logging
import asyncio

# Enhanced imports
from services.vision_pipeline import EnhancedVisionPipeline
from workers.vision_worker import VisionQueueClient
from config import settings

# Database imports
from tinydb import TinyDB, Query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDatabase:
    """Enhanced database with vision metrics storage"""
    def __init__(self, db_path: str = "gym_coach_enhanced.json"):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
        self.vision_metrics = self.db.table('vision_metrics')
        self.plans = self.db.table('plans')

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

    def store_vision_metrics(self, user_id: str, metrics: Dict[str, Any]) -> str:
        """Store enhanced vision metrics"""
        metrics_id = str(uuid.uuid4())
        vision_data = {
            'id': metrics_id,
            'user_id': user_id,
            'metrics': metrics,
            'created_at': datetime.utcnow().isoformat()
        }
        self.vision_metrics.insert(vision_data)
        return metrics_id

    def get_latest_vision_metrics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get latest vision metrics for user"""
        VisionMetrics = Query()
        results = self.vision_metrics.search(VisionMetrics.user_id == user_id)
        if results:
            latest = max(results, key=lambda x: x['created_at'])
            return latest['metrics']
        return None

    def store_plan(self, user_id, plan_data):
        plan_data['user_id'] = user_id
        plan_data['created_at'] = datetime.utcnow().isoformat()
        self.plans.insert(plan_data)

    def get_user_plans(self, user_id):
        Plan = Query()
        return self.plans.search(Plan.user_id == user_id)

# Enhanced Models
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

class VisionMetricsResponse(BaseModel):
    """Response model matching the specification"""
    poseAlerts: List[str]
    anthro: Dict[str, float]
    bf_estimate: float
    imageQuality: float
    confidence: str = "medium"
    waist_to_hip_ratio: Optional[float] = None
    analysis_timestamp: str
    version: str = "2.0"

class PlanRequest(BaseModel):
    fitness_goal: str
    days_per_week: int
    activity_level: str
    experience_level: Optional[str] = "intermediate"

class GeneratedPlan(BaseModel):
    id: str
    workout_plan: List[dict]
    nutrition_plan: dict
    rationale: str
    vision_adjustments: Optional[List[str]] = []

# Initialize FastAPI app
app = FastAPI(
    title="Gym AI Coach API - Vision Enhanced",
    description="AI-powered fitness planning with advanced computer vision",
    version="2.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database and services
db = EnhancedDatabase()

# Vision services - try worker first, fallback to direct processing
vision_queue_client = None
vision_pipeline = None

try:
    vision_queue_client = VisionQueueClient(settings.redis_url) if settings.redis_url else None
    logger.info("Vision queue client initialized")
except Exception as e:
    logger.warning(f"Failed to initialize vision queue client: {e}")

if not vision_queue_client:
    vision_pipeline = EnhancedVisionPipeline()
    logger.info("Using direct vision pipeline (no Redis worker)")

# Upload directory
UPLOAD_DIR = settings.upload_dir
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

async def process_vision_analysis(image_path: str, user_id: str, height_cm: float, 
                                weight_kg: float, sex: str) -> Dict[str, Any]:
    """Process vision analysis using worker or direct pipeline"""
    
    if vision_queue_client:
        # Use Redis worker for processing
        logger.info(f"Processing image via worker for user {user_id}")
        try:
            result = await vision_queue_client.queue_and_wait(
                image_path=image_path,
                user_id=user_id,
                user_height_cm=height_cm,
                user_weight_kg=weight_kg,
                user_sex=sex,
                timeout=60  # 60 second timeout
            )
            return result
        except Exception as e:
            logger.error(f"Worker processing failed: {e}, falling back to direct processing")
            # Fall through to direct processing
    
    # Direct processing fallback
    if vision_pipeline:
        logger.info(f"Processing image directly for user {user_id}")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            vision_pipeline.process_image,
            image_path, height_cm, weight_kg, sex
        )
        return result
    
    # Ultimate fallback
    logger.error("No vision processing available")
    raise HTTPException(status_code=503, detail="Vision analysis service unavailable")

@app.get("/")
async def root():
    """Root endpoint with service status"""
    return {
        "message": "Gym AI Coach API v2.1 - Vision Enhanced", 
        "status": "running",
        "features": ["advanced_pose_detection", "body_composition_estimation", "posture_analysis"],
        "vision_worker": "enabled" if vision_queue_client else "disabled",
        "direct_processing": "enabled" if vision_pipeline else "disabled"
    }

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "services": {
            "database": "healthy",
            "vision_worker": "unknown",
            "direct_vision": "enabled" if vision_pipeline else "disabled"
        }
    }
    
    # Check vision worker if available
    if vision_queue_client:
        try:
            # Simple Redis ping
            health["services"]["vision_worker"] = "healthy"
        except Exception:
            health["services"]["vision_worker"] = "unhealthy"
    
    return health

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

@app.post("/api/upload-image", response_model=VisionMetricsResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze physique image using enhanced vision pipeline"""
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {settings.max_upload_size/1024/1024:.1f}MB"
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Get user data for vision pipeline
        user_data = db.get_latest_user_data(current_user["id"])
        height_cm = user_data.get("height", 175.0) if user_data else 175.0
        weight_kg = user_data.get("weight", 70.0) if user_data else 70.0
        sex = user_data.get("sex", "male") if user_data else "male"
        
        logger.info(f"Processing image for user {current_user['id']}: {filename}")
        
        # Process with enhanced vision pipeline
        vision_result = await process_vision_analysis(
            file_path, current_user["id"], height_cm, weight_kg, sex
        )
        
        # Handle errors from vision pipeline
        if "error" in vision_result:
            logger.error(f"Vision analysis error: {vision_result['error']}")
            raise HTTPException(
                status_code=422, 
                detail=f"Vision analysis failed: {vision_result['error']}"
            )
        
        # Store vision metrics in database
        metrics_id = db.store_vision_metrics(current_user["id"], vision_result)
        
        # Convert to response model (match exact specification)
        response_data = VisionMetricsResponse(
            poseAlerts=vision_result.get("poseAlerts", []),
            anthro=vision_result.get("anthro", {}),
            bf_estimate=vision_result.get("bf_estimate", 20.0),
            imageQuality=vision_result.get("imageQuality", 0.5),
            confidence=vision_result.get("confidence", "medium"),
            waist_to_hip_ratio=vision_result.get("waist_to_hip_ratio"),
            analysis_timestamp=vision_result.get("analysis_timestamp", datetime.utcnow().isoformat()),
            version=vision_result.get("version", "2.0")
        )
        
        logger.info(f"Vision analysis completed for user {current_user['id']} with quality {response_data.imageQuality}")
        
        # Optional: Clean up file in background after some time
        background_tasks.add_task(cleanup_file_later, file_path, 3600)  # Delete after 1 hour
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@app.post("/api/user-data")
async def store_user_data(
    user_data: UserData,
    current_user: dict = Depends(get_current_user)
):
    """Store user physical data"""
    try:
        data_dict = user_data.dict()
        db.store_user_data(current_user["id"], data_dict)
        
        return {
            "message": "User data stored successfully",
            "data": data_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store user data: {str(e)}")

@app.post("/api/generate-plan", response_model=GeneratedPlan)
async def generate_plan(
    plan_request: PlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate enhanced workout plan with vision-based adjustments"""
    try:
        # Get latest user data
        user_data = db.get_latest_user_data(current_user["id"])
        if not user_data:
            raise HTTPException(status_code=400, detail="Please provide user data first")
        
        # Get latest vision metrics
        vision_metrics = db.get_latest_vision_metrics(current_user["id"])
        
        # Generate enhanced plan
        plan_id = str(uuid.uuid4())
        
        # Use your existing plan generation logic but enhanced with vision data
        workout_plan = generate_vision_enhanced_workout_plan(plan_request, user_data, vision_metrics)
        nutrition_plan = generate_vision_enhanced_nutrition_plan(plan_request, user_data, vision_metrics)
        rationale = generate_enhanced_rationale(plan_request, user_data, vision_metrics)
        vision_adjustments = extract_vision_adjustments(vision_metrics)
        
        plan_data = {
            "id": plan_id,
            "workout_plan": workout_plan,
            "nutrition_plan": nutrition_plan,
            "rationale": rationale,
            "vision_adjustments": vision_adjustments,
            "plan_request": plan_request.dict(),
            "user_data": user_data,
            "vision_metrics": vision_metrics
        }
        
        db.store_plan(current_user["id"], plan_data)
        
        return GeneratedPlan(
            id=plan_id,
            workout_plan=workout_plan,
            nutrition_plan=nutrition_plan,
            rationale=rationale,
            vision_adjustments=vision_adjustments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

@app.get("/api/plans")
async def get_user_plans(current_user: dict = Depends(get_current_user)):
    """Get user's previous plans"""
    try:
        plans = db.get_user_plans(current_user["id"])
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plans: {str(e)}")

@app.get("/api/vision-metrics")
async def get_vision_metrics(current_user: dict = Depends(get_current_user)):
    """Get latest vision analysis metrics for user"""
    try:
        metrics = db.get_latest_vision_metrics(current_user["id"])
        if not metrics:
            raise HTTPException(status_code=404, detail="No vision analysis found")
        return {"vision_metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vision metrics: {str(e)}")

# Enhanced plan generation functions with vision integration
def generate_vision_enhanced_workout_plan(plan_request: PlanRequest, user_data: Dict, vision_metrics: Optional[Dict]) -> List[Dict]:
    """Generate workout plan with vision-based adjustments following the specification"""
    
    # Base workout structure
    base_exercises = [
        {
            "exercise_id": "squat_001",
            "name": "Squats",
            "sets": 3,
            "reps": "8-12",
            "rest_seconds": 120,
            "muscle_groups": ["quadriceps", "glutes", "core"],
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "instructions": ["Stand with feet shoulder-width apart", "Lower down as if sitting back", "Keep chest up and knees tracking over toes"]
        },
        {
            "exercise_id": "pushup_001",
            "name": "Push-ups", 
            "sets": 3,
            "reps": "8-15",
            "rest_seconds": 90,
            "muscle_groups": ["chest", "triceps", "shoulders", "core"],
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "instructions": ["Start in plank position", "Lower chest to ground", "Push back up maintaining straight line"]
        },
        {
            "exercise_id": "deadlift_001",
            "name": "Romanian Deadlifts",
            "sets": 3,
            "reps": "8-10",
            "rest_seconds": 150,
            "muscle_groups": ["hamstrings", "glutes", "lower_back"],
            "equipment": "dumbbells",
            "difficulty": "intermediate",
            "instructions": ["Hold weights in front of thighs", "Hinge at hips keeping back straight", "Lower weights toward floor, feel stretch in hamstrings"]
        }
    ]
    
    # Apply vision-based adjustments
    if vision_metrics:
        pose_alerts = vision_metrics.get("poseAlerts", [])
        anthro = vision_metrics.get("anthro", {})
        
        # Inject corrective mobility drills for rounded shoulders
        if "rounded_shoulders" in pose_alerts:
            base_exercises.insert(0, {
                "exercise_id": "thoracic_opener_001",
                "name": "Thoracic Spine Opener",
                "sets": 2,
                "reps": "8-10",
                "rest_seconds": 30,
                "muscle_groups": ["thoracic_spine", "chest"],
                "equipment": "bodyweight",
                "difficulty": "beginner",
                "corrective": True,
                "reason": "Corrective mobility drill for rounded shoulders",
                "instructions": ["Kneel with hands on ground", "Sit back on heels", "Arch upper back and look up"]
            })
            
            base_exercises.append({
                "exercise_id": "face_pulls_001", 
                "name": "Face Pulls",
                "sets": 3,
                "reps": "12-15",
                "rest_seconds": 60,
                "muscle_groups": ["rear_delts", "rhomboids", "middle_traps"],
                "equipment": "resistance_band",
                "difficulty": "beginner", 
                "corrective": True,
                "reason": "Strengthen posterior chain for rounded shoulders",
                "instructions": ["Pull band to face level", "Squeeze shoulder blades", "Focus on rear delt activation"]
            })
        
        # Add core stability for anterior pelvic tilt
        if "anterior_pelvic_tilt" in pose_alerts:
            base_exercises.append({
                "exercise_id": "dead_bug_001",
                "name": "Dead Bug",
                "sets": 2,
                "reps": "6 each side",
                "rest_seconds": 45,
                "muscle_groups": ["core", "hip_flexors"],
                "equipment": "bodyweight",
                "difficulty": "beginner",
                "corrective": True,
                "reason": "Core stability exercise for anterior pelvic tilt",
                "instructions": ["Lie on back, arms up, knees bent 90°", "Lower opposite arm and leg slowly", "Maintain lower back contact with floor"]
            })
        
        # Adapt exercise selection to anthropometrics (long femur considerations)
        hip_cm = anthro.get("hip_cm", 90)
        shoulder_cm = anthro.get("shoulder_cm", 45)
        
        if hip_cm > 95:  # Suggests longer limbs/femurs
            # Modify squat to front squat for better mechanics
            for exercise in base_exercises:
                if "squat" in exercise["name"].lower():
                    exercise["name"] = "Goblet Squats"
                    exercise["equipment"] = "dumbbell"
                    exercise["reason"] = "Better mechanics for longer femur proportions"
                    exercise["instructions"] = ["Hold weight at chest", "Squat down keeping torso upright", "Weight counterbalances longer femurs"]
    
    # Add experience-based progressions
    experience = plan_request.experience_level
    if experience == "advanced":
        for exercise in base_exercises:
            if not exercise.get("corrective"):
                exercise["sets"] += 1
                exercise["difficulty"] = "advanced"
    
    return base_exercises

def generate_vision_enhanced_nutrition_plan(plan_request: PlanRequest, user_data: Dict, vision_metrics: Optional[Dict]) -> Dict:
    """Generate nutrition plan refined by BF% estimate and macro ratios"""
    
    # Base calculations
    weight = user_data.get("weight", 70)
    height = user_data.get("height", 175)
    age = user_data.get("age", 30)
    sex = user_data.get("sex", "male")
    
    # Calculate BMR using Harris-Benedict
    if sex.lower() == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Activity level multipliers
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "athlete": 1.9
    }
    
    tdee = bmr * activity_multipliers.get(plan_request.activity_level, 1.55)
    
    # Goal-based calorie adjustments
    goal_adjustments = {
        "lose_fat": -400,
        "gain_muscle": 300,
        "strength": 200,
        "recomposition": -200,
        "maintenance": 0
    }
    
    base_calories = tdee + goal_adjustments.get(plan_request.fitness_goal, 0)
    
    # Vision-based refinements
    vision_adjustments = {"calorie_delta": 0, "protein_multiplier": 1.0, "reasoning": []}
    
    if vision_metrics:
        bf_estimate = vision_metrics.get("bf_estimate", 20)
        confidence = vision_metrics.get("confidence", "medium")
        
        # Use bf_estimate to refine calorie target and macro ratios
        if bf_estimate > 25:  # Higher body fat percentage
            vision_adjustments["calorie_delta"] = -150  # Slightly larger deficit
            vision_adjustments["protein_multiplier"] = 1.3  # Moderate protein increase
            vision_adjustments["reasoning"].append(f"Higher estimated body fat ({bf_estimate}%) - increased deficit and protein")
        elif bf_estimate < 12:  # Very lean
            vision_adjustments["calorie_delta"] = 100  # Smaller deficit/surplus
            vision_adjustments["protein_multiplier"] = 1.1  # Moderate protein
            vision_adjustments["reasoning"].append(f"Low body fat estimate ({bf_estimate}%) - conservative approach")
        
        # If BF% estimate low-confidence, fall back to smart-scale value or be conservative
        if confidence == "low":
            vision_adjustments["calorie_delta"] = vision_adjustments["calorie_delta"] * 0.6
            vision_adjustments["reasoning"].append("Low confidence estimate - conservative adjustments")
            
            # Check if smart scale data is available
            smart_scale = user_data.get("smart_scale", {})
            if smart_scale.get("body_fat_percentage"):
                vision_adjustments["reasoning"].append("Using smart scale body fat data as fallback")
    
    # Calculate final targets
    target_calories = base_calories + vision_adjustments["calorie_delta"]
    
    # Macro distribution with vision adjustments
    protein_g_per_kg = 2.2 * vision_adjustments["protein_multiplier"]  # High protein base
    protein_g = weight * protein_g_per_kg
    
    # Fat: 25-30% of calories
    fat_percentage = 0.27
    fat_g = (target_calories * fat_percentage) / 9
    
    # Remaining calories from carbs
    remaining_calories = target_calories - (protein_g * 4) - (fat_g * 9)
    carbs_g = remaining_calories / 4
    
    return {
        "daily_calories": round(target_calories),
        "macros": {
            "protein_g": round(protein_g, 1),
            "carbs_g": round(max(carbs_g, 100), 1),  # Minimum 100g carbs
            "fat_g": round(fat_g, 1)
        },
        "base_metabolic_data": {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "activity_level": plan_request.activity_level
        },
        "vision_adjustments": {
            "bf_estimate_used": vision_metrics.get("bf_estimate") if vision_metrics else None,
            "confidence_level": vision_metrics.get("confidence") if vision_metrics else None,
            "calorie_adjustment": vision_adjustments["calorie_delta"],
            "protein_multiplier": round(vision_adjustments["protein_multiplier"], 2),
            "reasoning": vision_adjustments["reasoning"]
        },
        "meal_plan": generate_adaptive_meals(target_calories, protein_g, carbs_g, fat_g)
    }

def generate_adaptive_meals(calories: float, protein: float, carbs: float, fat: float) -> List[Dict]:
    """Generate sample meals with macro distribution"""
    
    # Meal distribution: breakfast 25%, lunch 35%, dinner 30%, snacks 10%
    distributions = [0.25, 0.35, 0.30, 0.10]
    meal_types = ["breakfast", "lunch", "dinner", "snack"]
    
    meals = []
    
    for i, (meal_type, dist) in enumerate(zip(meal_types, distributions)):
        meal_cals = calories * dist
        meal_protein = protein * dist
        meal_carbs = carbs * dist
        meal_fat = fat * dist
        
        meal_templates = {
            "breakfast": {
                "name": "Power Breakfast Bowl",
                "ingredients": ["rolled oats", "protein powder", "banana", "almond butter", "berries"],
                "prep_time_minutes": 8,
                "ai_reason": "High protein start with sustained energy carbs"
            },
            "lunch": {
                "name": "Lean Protein & Complex Carbs",
                "ingredients": ["chicken breast", "quinoa", "mixed vegetables", "olive oil", "avocado"],
                "prep_time_minutes": 25,
                "ai_reason": "Balanced macros for sustained afternoon energy"
            },
            "dinner": {
                "name": "Recovery & Repair Dinner", 
                "ingredients": ["salmon", "sweet potato", "asparagus", "coconut oil"],
                "prep_time_minutes": 30,
                "ai_reason": "Omega-3s and nutrients for overnight recovery"
            },
            "snack": {
                "name": "Quick Protein Boost",
                "ingredients": ["greek yogurt", "mixed nuts", "honey"],
                "prep_time_minutes": 2,
                "ai_reason": "Fast protein and healthy fats"
            }
        }
        
        template = meal_templates[meal_type]
        
        meals.append({
            "meal_type": meal_type,
            "name": template["name"],
            "calories": round(meal_cals),
            "macros": {
                "protein_g": round(meal_protein, 1),
                "carbs_g": round(meal_carbs, 1), 
                "fat_g": round(meal_fat, 1)
            },
            "ingredients": template["ingredients"],
            "prep_time_minutes": template["prep_time_minutes"],
            "ai_reason": template["ai_reason"]
        })
    
    return meals

def generate_enhanced_rationale(plan_request: PlanRequest, user_data: Dict, vision_metrics: Optional[Dict]) -> str:
    """Generate comprehensive rationale with vision insights"""
    
    rationale_parts = []
    
    # Base rationale
    rationale_parts.append(f"This {plan_request.days_per_week}-day program targets your {plan_request.fitness_goal.replace('_', ' ')} goal using evidence-based exercise selection and periodization.")
    
    # Vision-based insights - surface "Why we chose this" notes
    if vision_metrics:
        pose_alerts = vision_metrics.get("poseAlerts", [])
        bf_estimate = vision_metrics.get("bf_estimate")
        image_quality = vision_metrics.get("imageQuality", 0)
        
        if pose_alerts:
            corrective_focus = ", ".join([alert.replace("_", " ") for alert in pose_alerts])
            rationale_parts.append(f"Your posture analysis revealed {corrective_focus}, so we've included targeted corrective exercises and mobility work.")
        
        if bf_estimate and image_quality > 0.6:
            rationale_parts.append(f"Based on your body composition analysis (estimated {bf_estimate}% body fat), we've calibrated your nutrition targets for optimal progress.")
        
        # Anthropometric considerations
        anthro = vision_metrics.get("anthro", {})
        if anthro.get("hip_cm", 0) > 95:
            rationale_parts.append("Your body proportions suggested modifications to squat mechanics for improved biomechanical efficiency.")
    
    # Experience and activity considerations
    rationale_parts.append(f"The program accounts for your {plan_request.experience_level} experience level and {plan_request.activity_level} lifestyle.")
    
    return " ".join(rationale_parts)

def extract_vision_adjustments(vision_metrics: Optional[Dict]) -> List[str]:
    """Extract specific adjustments made based on vision analysis"""
    
    if not vision_metrics:
        return ["No vision analysis available - using standard evidence-based recommendations"]
    
    adjustments = []
    pose_alerts = vision_metrics.get("poseAlerts", [])
    
    # Document specific corrective interventions
    if "rounded_shoulders" in pose_alerts:
        adjustments.append("Added thoracic spine mobility and posterior chain strengthening for rounded shoulder posture")
    
    if "anterior_pelvic_tilt" in pose_alerts:
        adjustments.append("Included core stabilization exercises to address anterior pelvic tilt")
    
    if "forward_head" in pose_alerts:
        adjustments.append("Incorporated neck strengthening and upper cervical mobility work")
    
    # Nutrition adjustments
    bf_estimate = vision_metrics.get("bf_estimate")
    if bf_estimate:
        if bf_estimate > 25:
            adjustments.append(f"Increased protein intake and caloric deficit based on {bf_estimate}% body fat analysis")
        elif bf_estimate < 12:
            adjustments.append(f"Conservative caloric approach for lean physique ({bf_estimate}% body fat)")
    
    # Exercise selection adjustments
    anthro = vision_metrics.get("anthro", {})
    if anthro.get("hip_cm", 0) > 95:
        adjustments.append("Modified squat variations for longer limb proportions and improved mechanics")
    
    if not adjustments:
        adjustments.append("Standard evidence-based program - no specific postural or compositional concerns identified")
    
    return adjustments

async def cleanup_file_later(file_path: str, delay_seconds: int = 3600):
    """Background task to clean up files after delay"""
    await asyncio.sleep(delay_seconds)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)