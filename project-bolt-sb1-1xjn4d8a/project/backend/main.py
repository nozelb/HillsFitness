# backend/main.py - Enhanced with Vision Pipeline
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

# Enhanced imports
from services.vision_pipeline import EnhancedVisionPipeline
from services.image_service import ImageService
from config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Database imports
from tinydb import TinyDB, Query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDatatabase:
    """Enhanced database with vision metrics storage"""
    def __init__(self, db_path: str = "gym_coach_enhanced.json"):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
        self.vision_metrics = self.db.table('vision_metrics')  # New table
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

class EnhancedImageAnalysisResult(BaseModel):
    """Enhanced result model matching vision pipeline output"""
    pose_alerts: List[str]
    anthro: Dict[str, float]
    bf_estimate: float
    image_quality: float
    confidence: str
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
    vision_adjustments: Optional[List[str]] = []  # New field

# Initialize FastAPI app
app = FastAPI(
    title="Gym AI Coach API Enhanced",
    description="AI-powered fitness planning with advanced vision analysis",
    version="2.1.0"
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
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database
db = SimpleDatatabase()

# Enhanced services
vision_pipeline = EnhancedVisionPipeline()
image_service = ImageService()

# Thread pool for CPU-intensive vision processing
executor = ThreadPoolExecutor(max_workers=2)

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

def run_vision_pipeline_sync(image_path: str, height_cm: float, weight_kg: float, sex: str) -> Dict[str, Any]:
    """Synchronous wrapper for vision pipeline to run in thread pool"""
    return vision_pipeline.process_image(image_path, height_cm, weight_kg, sex)

async def process_image_async(image_path: str, height_cm: float, weight_kg: float, sex: str) -> Dict[str, Any]:
    """Async wrapper for vision pipeline processing"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor, 
        run_vision_pipeline_sync, 
        image_path, height_cm, weight_kg, sex
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Gym AI Coach API v2.1 - Enhanced Vision Pipeline", 
        "status": "running",
        "features": ["advanced_pose_detection", "body_composition_estimation", "posture_analysis"]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "vision_pipeline": "enabled"
    }

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

@app.post("/api/upload-image", response_model=EnhancedImageAnalysisResult)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Enhanced image upload with advanced vision pipeline"""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {settings.max_upload_size/1024/1024:.1f}MB"
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Get user data for vision pipeline
        user_data = db.get_latest_user_data(current_user["id"])
        if not user_data:
            # Use default values if no user data
            height_cm = 175.0
            weight_kg = 70.0
            sex = "male"
        else:
            height_cm = user_data.get("height", 175.0)
            weight_kg = user_data.get("weight", 70.0)
            sex = user_data.get("sex", "male")
        
        logger.info(f"Processing image for user {current_user['id']}: {filename}")
        
        # Run enhanced vision pipeline asynchronously
        vision_result = await process_image_async(file_path, height_cm, weight_kg, sex)
        
        # Store vision metrics in database
        metrics_id = db.store_vision_metrics(current_user["id"], vision_result)
        
        # Clean up file in background (optional - you might want to keep files)
        # background_tasks.add_task(cleanup_file, file_path)
        
        # Convert to response model
        response_data = EnhancedImageAnalysisResult(
            pose_alerts=vision_result.get("poseAlerts", []),
            anthro=vision_result.get("anthro", {}),
            bf_estimate=vision_result.get("bf_estimate", 20.0),
            image_quality=vision_result.get("imageQuality", 0.5),
            confidence=vision_result.get("confidence", "medium"),
            waist_to_hip_ratio=vision_result.get("waist_to_hip_ratio"),
            analysis_timestamp=vision_result.get("analysis_timestamp", datetime.utcnow().isoformat()),
            version=vision_result.get("version", "2.0")
        )
        
        logger.info(f"Vision analysis completed for user {current_user['id']}")
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
        
        # Generate base plan (your existing logic)
        plan_id = str(uuid.uuid4())
        
        # Enhanced workout plan with vision adjustments
        workout_plan = generate_enhanced_workout_plan(
            plan_request, user_data, vision_metrics
        )
        
        # Enhanced nutrition plan with vision adjustments  
        nutrition_plan = generate_enhanced_nutrition_plan(
            plan_request, user_data, vision_metrics
        )
        
        # Generate rationale with vision insights
        rationale = generate_plan_rationale(
            plan_request, user_data, vision_metrics
        )
        
        # List of vision-based adjustments made
        vision_adjustments = generate_vision_adjustments(vision_metrics)
        
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

# Enhanced plan generation functions
def generate_enhanced_workout_plan(plan_request: PlanRequest, user_data: Dict, vision_metrics: Optional[Dict]) -> List[Dict]:
    """Generate workout plan with vision-based adjustments"""
    
    # Base workout plan
    base_exercises = [
        {
            "name": "Squats",
            "sets": 3,
            "reps": "8-12",
            "rest_seconds": 120,
            "muscle_groups": ["quadriceps", "glutes"],
            "equipment": "bodyweight"
        },
        {
            "name": "Push-ups",
            "sets": 3,
            "reps": "8-15",
            "rest_seconds": 90,
            "muscle_groups": ["chest", "triceps", "shoulders"],
            "equipment": "bodyweight"
        },
        {
            "name": "Deadlifts",
            "sets": 3,
            "reps": "6-10",
            "rest_seconds": 150,
            "muscle_groups": ["hamstrings", "glutes", "back"],
            "equipment": "barbell"
        }
    ]
    
    # Apply vision-based adjustments
    if vision_metrics:
        pose_alerts = vision_metrics.get("poseAlerts", [])
        anthro = vision_metrics.get("anthro", {})
        
        # Adjust for rounded shoulders
        if "rounded_shoulders" in pose_alerts:
            base_exercises.append({
                "name": "Face Pulls",
                "sets": 3,
                "reps": "12-15",
                "rest_seconds": 60,
                "muscle_groups": ["rear_delts", "rhomboids"],
                "equipment": "cable",
                "reason": "Corrective exercise for rounded shoulders"
            })
            
            base_exercises.append({
                "name": "Thoracic Spine Opener",
                "sets": 2,
                "reps": "10",
                "rest_seconds": 30,
                "muscle_groups": ["thoracic_spine"],
                "equipment": "bodyweight",
                "reason": "Mobility drill for rounded shoulders"
            })
        
        # Adjust for anterior pelvic tilt
        if "anterior_pelvic_tilt" in pose_alerts:
            base_exercises.append({
                "name": "Dead Bug",
                "sets": 2,
                "reps": "8 each side",
                "rest_seconds": 45,
                "muscle_groups": ["core", "hip_flexors"],
                "equipment": "bodyweight",
                "reason": "Core stability for anterior pelvic tilt"
            })
        
        # Adjust for long femur (if hip to knee ratio suggests it)
        hip_cm = anthro.get("hip_cm", 90)
        if hip_cm > 95:  # Suggests longer limbs
            # Modify squat recommendation
            for exercise in base_exercises:
                if exercise["name"] == "Squats":
                    exercise["name"] = "Front Squats"
                    exercise["reason"] = "Better for longer femur mechanics"
    
    return base_exercises

def generate_enhanced_nutrition_plan(plan_request: PlanRequest, user_data: Dict, vision_metrics: Optional[Dict]) -> Dict:
    """Generate nutrition plan with vision-based adjustments"""
    
    # Base calculations
    weight = user_data.get("weight", 70)
    height = user_data.get("height", 175)
    age = user_data.get("age", 30)
    sex = user_data.get("sex", "male")
    
    # Calculate BMR
    if sex.lower() == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Activity multiplier
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "athlete": 1.9
    }
    
    tdee = bmr * activity_multipliers.get(plan_request.activity_level, 1.55)
    
    # Adjust based on vision metrics
    calorie_adjustment = 0
    macro_adjustments = {"protein_multiplier": 1.0, "fat_multiplier": 1.0}
    
    if vision_metrics:
        bf_estimate = vision_metrics.get("bf_estimate", 20)
        confidence = vision_metrics.get("confidence", "medium")
        
        # Adjust calories based on body fat estimate
        if bf_estimate > 25:  # Higher body fat
            calorie_adjustment = -200  # Slightly larger deficit
            macro_adjustments["protein_multiplier"] = 1.2  # Higher protein
        elif bf_estimate < 12:  # Very low body fat
            calorie_adjustment = 100  # Smaller deficit or surplus
        
        # If low confidence, be more conservative
        if confidence == "low":
            calorie_adjustment = calorie_adjustment * 0.5
    
    # Goal-based adjustments
    goal_adjustments = {
        "lose_fat": -400,
        "gain_muscle": 300,
        "strength": 200,
        "recomposition": -200,
        "maintenance": 0
    }
    
    target_calories = tdee + goal_adjustments.get(plan_request.fitness_goal, 0) + calorie_adjustment
    
    # Macro distribution
    protein_g = (weight * 2.2 * macro_adjustments["protein_multiplier"])  # High protein
    fat_g = (target_calories * 0.25) / 9  # 25% from fat
    carbs_g = (target_calories - (protein_g * 4) - (fat_g * 9)) / 4
    
    return {
        "daily_calories": round(target_calories),
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1),
        "bmr": round(bmr),
        "tdee": round(tdee),
        "vision_adjustments": {
            "calorie_adjustment": calorie_adjustment,
            "reason": f"Based on {vision_metrics.get('confidence', 'medium')} confidence body fat estimate of {vision_metrics.get('bf_estimate', 'unknown')}%" if vision_metrics else "No vision data available"
        },
        "meals": generate_sample_meals(target_calories, protein_g, carbs_g, fat_g)
    }

def generate_sample_meals(calories: float, protein: float, carbs: float, fat: float) -> List[Dict]:
    """Generate sample meals based on macro targets"""
    meals = []
    meal_types = ["breakfast", "lunch", "dinner", "snack"]
    calorie_distribution = [0.25, 0.35, 0.30, 0.10]
    
    for i, meal_type in enumerate(meal_types):
        meal_calories = calories * calorie_distribution[i]
        meal_protein = protein * calorie_distribution[i]
        meal_carbs = carbs * calorie_distribution[i]
        meal_fat = fat * calorie_distribution[i]
        
        if meal_type == "breakfast":
            meal = {
                "meal_type": "breakfast",
                "name": "Protein Power Breakfast",
                "calories": meal_calories,
                "protein_g": meal_protein,
                "carbs_g": meal_carbs,
                "fat_g": meal_fat,
                "ingredients": ["oats", "protein powder", "banana", "almond butter"],
                "prep_time_minutes": 10
            }
        elif meal_type == "lunch":
            meal = {
                "meal_type": "lunch",
                "name": "Balanced Power Lunch",
                "calories": meal_calories,
                "protein_g": meal_protein,
                "carbs_g": meal_carbs,
                "fat_g": meal_fat,
                "ingredients": ["chicken breast", "quinoa", "mixed vegetables", "olive oil"],
                "prep_time_minutes": 20
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
                "prep_time_minutes": 30
            }
        else:  # snack
            meal = {
                "meal_type": "snack",
                "name": "Recovery Snack",
                "calories": meal_calories,
                "protein_g": meal_protein,
                "carbs_g": meal_carbs,
                "fat_g": meal_fat,
                "ingredients": ["greek yogurt", "berries", "almonds"],
                "prep_time_minutes": 5
            }
        
        meals.append(meal)
    
    return meals

def generate_plan_rationale(plan_request: PlanRequest, user_data: Dict, vision_metrics: Optional[Dict]) -> str:
    """Generate comprehensive plan rationale including vision insights"""
    
    rationale_parts = []
    
    # Base rationale
    rationale_parts.append(f"This {plan_request.days_per_week}-day plan is designed for your {plan_request.fitness_goal} goal.")
    
    # Vision-based insights
    if vision_metrics:
        pose_alerts = vision_metrics.get("poseAlerts", [])
        bf_estimate = vision_metrics.get("bf_estimate")
        confidence = vision_metrics.get("confidence", "medium")
        
        if pose_alerts:
            rationale_parts.append(f"Based on your posture analysis, we've included corrective exercises for: {', '.join(pose_alerts).replace('_', ' ')}.")
        
        if bf_estimate:
            rationale_parts.append(f"Your estimated body fat percentage ({bf_estimate}%) with {confidence} confidence has been used to adjust your nutrition targets.")
        
        anthro = vision_metrics.get("anthro", {})
        if anthro.get("hip_cm", 0) > 95:
            rationale_parts.append("Based on your body proportions, we've adjusted exercise selection for optimal biomechanics.")
    
    # Activity level consideration
    rationale_parts.append(f"Your {plan_request.activity_level} activity level has been factored into your calorie and macro targets.")
    
    return " ".join(rationale_parts)

def generate_vision_adjustments(vision_metrics: Optional[Dict]) -> List[str]:
    """Generate list of adjustments made based on vision analysis"""
    adjustments = []
    
    if not vision_metrics:
        return ["No vision analysis data available - using standard recommendations"]
    
    pose_alerts = vision_metrics.get("poseAlerts", [])
    bf_estimate = vision_metrics.get("bf_estimate")
    anthro = vision_metrics.get("anthro", {})
    
    # Posture-based adjustments
    if "rounded_shoulders" in pose_alerts:
        adjustments.append("Added corrective exercises (face pulls, thoracic openers) for rounded shoulders")
    
    if "anterior_pelvic_tilt" in pose_alerts:
        adjustments.append("Included core stability exercises to address anterior pelvic tilt")
    
    if "forward_head" in pose_alerts:
        adjustments.append("Added neck strengthening exercises for forward head posture")
    
    # Body composition adjustments
    if bf_estimate:
        if bf_estimate > 25:
            adjustments.append(f"Increased protein target and calorie deficit based on {bf_estimate}% body fat estimate")
        elif bf_estimate < 12:
            adjustments.append(f"Adjusted for lean physique ({bf_estimate}% body fat) - reduced calorie deficit")
    
    # Anthropometric adjustments
    if anthro.get("hip_cm", 0) > 95:
        adjustments.append("Modified squat variation for longer limb proportions")
    
    if not adjustments:
        adjustments.append("No specific adjustments needed - standard evidence-based plan applied")
    
    return adjustments

def cleanup_file(file_path: str):
    """Background task to clean up uploaded files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)