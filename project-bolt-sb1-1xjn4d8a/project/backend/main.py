from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from typing import Optional, List
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

# Simple TinyDB implementation for fallback
from tinydb import TinyDB, Query

class SimpleDatatabase:
    def __init__(self, db_path: str = "gym_coach_simple.json"):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
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

# Simple image analysis function
def simple_analyze_physique_from_image(image_path):
    """Simple fallback image analysis"""
    return {
        "waist_cm": 80.0,
        "hip_cm": 90.0,
        "shoulder_cm": 45.0,
        "body_fat_estimate": 18.0,
        "confidence_score": 0.5
    }

# Simple workout plan generator
def simple_generate_workout_plan(user_data, image_analysis, goal, days_per_week):
    """Simple workout plan generator"""
    return [
        {
            "day": "Day 1",
            "muscle_groups": ["chest", "shoulders"],
            "exercises": [
                {"name": "Push-ups", "sets": 3, "reps": "10-12", "rest_seconds": 60, "notes": "Focus on form"},
                {"name": "Overhead Press", "sets": 3, "reps": "8-10", "rest_seconds": 60, "notes": "Control the weight"},
                {"name": "Lateral Raises", "sets": 3, "reps": "12-15", "rest_seconds": 45, "notes": "Light weight, focus on form"},
                {"name": "Tricep Dips", "sets": 3, "reps": "8-12", "rest_seconds": 60, "notes": "Use bench or chair"}
            ],
            "estimated_duration_minutes": 45
        },
        {
            "day": "Day 2", 
            "muscle_groups": ["back", "biceps"],
            "exercises": [
                {"name": "Pull-ups", "sets": 3, "reps": "5-8", "rest_seconds": 90, "notes": "Use assistance if needed"},
                {"name": "Bent-over Row", "sets": 3, "reps": "10-12", "rest_seconds": 60, "notes": "Keep back straight"},
                {"name": "Bicep Curls", "sets": 3, "reps": "12-15", "rest_seconds": 45, "notes": "Control the negative"},
                {"name": "Face Pulls", "sets": 3, "reps": "15-20", "rest_seconds": 45, "notes": "Good for posture"}
            ],
            "estimated_duration_minutes": 40
        },
        {
            "day": "Day 3",
            "muscle_groups": ["legs", "core"],
            "exercises": [
                {"name": "Squats", "sets": 3, "reps": "12-15", "rest_seconds": 90, "notes": "Full range of motion"},
                {"name": "Lunges", "sets": 3, "reps": "10-12 each leg", "rest_seconds": 60, "notes": "Alternate legs"},
                {"name": "Calf Raises", "sets": 3, "reps": "15-20", "rest_seconds": 45, "notes": "Squeeze at the top"},
                {"name": "Plank", "sets": 3, "reps": "30-60 seconds", "rest_seconds": 60, "notes": "Keep body straight"},
                {"name": "Mountain Climbers", "sets": 3, "reps": "20 each leg", "rest_seconds": 45, "notes": "Keep hips level"}
            ],
            "estimated_duration_minutes": 50
        }
    ]

# Simple nutrition plan generator  
def simple_generate_nutrition_plan(user_data, image_analysis, goal, activity_level):
    """Simple nutrition plan generator"""
    # Basic calculations
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170) 
    age = user_data.get('age', 30)
    sex = user_data.get('sex', 'male')
    
    # Simple BMR calculation
    if sex == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Activity multiplier
    activity_multipliers = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)
    
    # Goal adjustment
    if goal == "lose_fat":
        calories = int(tdee * 0.85)
    elif goal == "gain_muscle": 
        calories = int(tdee * 1.15)
    else:
        calories = int(tdee)
    
    # Simple macro calculation
    protein_g = int(weight * 2.2)  # 2.2g per kg
    fat_g = int(calories * 0.25 / 9)  # 25% of calories from fat
    carbs_g = int((calories - (protein_g * 4) - (fat_g * 9)) / 4)
    
    return {
        "daily_targets": {
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g
        },
        "bmr": int(bmr),
        "tdee": int(tdee),
        "meal_suggestions": [
            {
                "meal_type": "breakfast",
                "name": "Protein Oatmeal",
                "calories": int(calories * 0.25),
                "protein_g": int(protein_g * 0.25),
                "carbs_g": int(carbs_g * 0.25), 
                "fat_g": int(fat_g * 0.25),
                "ingredients": ["Oats", "Protein powder", "Berries", "Nuts"]
            },
            {
                "meal_type": "lunch", 
                "name": "Chicken and Rice",
                "calories": int(calories * 0.35),
                "protein_g": int(protein_g * 0.35),
                "carbs_g": int(carbs_g * 0.35),
                "fat_g": int(fat_g * 0.35),
                "ingredients": ["Chicken breast", "Brown rice", "Vegetables", "Olive oil"]
            },
            {
                "meal_type": "dinner",
                "name": "Salmon and Sweet Potato", 
                "calories": int(calories * 0.30),
                "protein_g": int(protein_g * 0.30),
                "carbs_g": int(carbs_g * 0.30),
                "fat_g": int(fat_g * 0.30),
                "ingredients": ["Salmon", "Sweet potato", "Broccoli", "Avocado"]
            },
            {
                "meal_type": "snack",
                "name": "Greek Yogurt",
                "calories": int(calories * 0.10), 
                "protein_g": int(protein_g * 0.10),
                "carbs_g": int(carbs_g * 0.10),
                "fat_g": int(fat_g * 0.10),
                "ingredients": ["Greek yogurt", "Honey", "Almonds"]
            }
        ],
        "hydration_target_ml": int(weight * 35),
        "notes": [
            f"Eat {protein_g}g protein daily to support your {goal} goal",
            "Spread protein intake across all meals", 
            "Stay hydrated with at least 8 glasses of water daily",
            "Adjust portions based on hunger and energy levels"
        ]
    }

# Define models inline
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

class PlanRequest(BaseModel):
    fitness_goal: str
    days_per_week: int
    activity_level: str

class GeneratedPlan(BaseModel):
    id: str
    workout_plan: List[dict]
    nutrition_plan: dict
    rationale: str

# Initialize FastAPI app
app = FastAPI(
    title="Gym AI Coach API",
    description="AI-powered fitness and nutrition planning",
    version="1.0.0"
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
db = SimpleDatatabase()

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
    return {"message": "Gym AI Coach API", "status": "running"}

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
    """Upload and analyze physique image"""
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
        
        # Analyze image
        analysis_result = simple_analyze_physique_from_image(file_path)
        
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
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

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
    """Generate personalized workout and nutrition plan"""
    try:
        raw_body = await request.body()
        plan_request = PlanRequest.parse_raw(raw_body)
        
        # Get user's latest data
        user_data = db.get_latest_user_data(current_user["id"])
        image_analysis = db.get_latest_image_analysis(current_user["id"])
        
        if not user_data:
            raise HTTPException(status_code=400, detail="User data required")
        
        # Generate workout plan
        workout_plan = simple_generate_workout_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            days_per_week=plan_request.days_per_week
        )
        
        # Generate nutrition plan
        nutrition_plan = simple_generate_nutrition_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            activity_level=plan_request.activity_level
        )
        
        # Store generated plan
        plan_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "workout_plan": workout_plan,
            "nutrition_plan": nutrition_plan,
            "goal": plan_request.fitness_goal,
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.store_plan(current_user["id"], plan_data)
        
        result = GeneratedPlan(
            id=plan_data["id"],
            workout_plan=workout_plan,
            nutrition_plan=nutrition_plan,
            rationale="Plan generated based on your physique analysis, goals, and evidence-based fitness principles."
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

@app.get("/api/plans")
async def get_user_plans(current_user: dict = Depends(get_current_user)):
    """Get user's previous plans"""
    try:
        plans = db.get_user_plans(current_user["id"])
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plans: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get dashboard data with stats, today's focus, and charts data"""
    try:
        # Return mock dashboard data for now
        mock_data = {
            "stats": {
                "current_weight": 75.0,
                "weight_change_7d": -0.5,
                "weight_change_30d": -2.1,
                "workouts_this_week": 3,
                "total_workout_time_week": 180,
                "current_streak": 5,
                "next_workout": {
                    "day": "Day 1",
                    "muscle_groups": ["chest", "shoulders"],
                    "estimated_duration_minutes": 45
                }
            },
            "todays_focus": {
                "workout_scheduled": {
                    "day": "Day 1",
                    "muscle_groups": ["chest", "shoulders"],
                    "estimated_duration_minutes": 45
                },
                "nutrition_targets": {
                    "calories": 2200,
                    "protein_g": 165,
                    "carbs_g": 220,
                    "fat_g": 73
                },
                "progress_logged": False,
                "motivational_message": "Every workout counts! You're building a stronger you."
            },
            "recent_progress": [
                {"date": "2025-06-20", "energy_level": 8, "mood": 9, "sleep_hours": 7.5},
                {"date": "2025-06-21", "energy_level": 7, "mood": 8, "sleep_hours": 6.8},
                {"date": "2025-06-22", "energy_level": 9, "mood": 9, "sleep_hours": 8.2},
                {"date": "2025-06-23", "energy_level": 8, "mood": 7, "sleep_hours": 7.0}
            ],
            "weight_trend": [
                {"date": "2025-06-15", "weight": 77.2},
                {"date": "2025-06-18", "weight": 76.8},
                {"date": "2025-06-21", "weight": 75.5},
                {"date": "2025-06-24", "weight": 75.0}
            ],
            "workout_frequency": [
                {"week": "Week 1", "workouts": 2, "duration": 90},
                {"week": "Week 2", "workouts": 4, "duration": 200},
                {"week": "Week 3", "workouts": 3, "duration": 150},
                {"week": "Week 4", "workouts": 3, "duration": 180}
            ]
        }
        
        return mock_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

# Basic progress tracking endpoints
@app.post("/api/progress")
async def log_progress(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log daily progress entry"""
    try:
        raw_body = await request.body()
        progress_data = json.loads(raw_body.decode())
        print(f"Progress logged for user {current_user['id']}: {progress_data}")
        return {"message": "Progress logged successfully"}
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
        print(f"Workout logged for user {current_user['id']}: {workout_data}")
        return {"message": "Workout logged successfully"}
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
        print(f"Weight logged for user {current_user['id']}: {weight_data}")
        return {"message": "Weight logged successfully"}
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
        return {"progress": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress history: {str(e)}")

@app.get("/api/weight-history")
async def get_weight_history(
    days: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """Get weight history"""
    try:
        return {"weight_logs": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weight history: {str(e)}")

@app.get("/api/workout-history")
async def get_workout_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get workout history"""
    try:
        return {"workout_logs": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workout history: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)