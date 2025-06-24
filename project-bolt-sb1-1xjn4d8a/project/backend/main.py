from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
import os
import json
import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, List
import aiofiles
from PIL import Image
import io
from pydantic import ValidationError

from models import (
    UserCreate, UserLogin, UserResponse, UserData, 
    ImageAnalysisResult, PlanRequest, GeneratedPlan,
    ProgressEntry, WorkoutLog, WeightEntry, BodyMeasurements,
    DashboardResponse, DashboardStats, TodaysFocus
)
from image_utils import analyze_physique_from_image
from plan_engine import generate_workout_plan
from nutrition_engine import generate_nutrition_plan
from database import Database

# Initialize FastAPI app
app = FastAPI(
    title="Gym AI Coach API",
    description="AI-powered fitness and nutrition planning",
    version="1.0.0"
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
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
db = Database()

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
        print(f"DEBUG REGISTER: Attempting to register user: {user.email}")
        
        existing_user = db.get_user_by_email(user.email)
        if existing_user:
            print(f"DEBUG REGISTER: User already exists: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        print("DEBUG REGISTER: Hashing password...")
        hashed_password = get_password_hash(user.password)
        
        user_data = {
            "id": str(uuid.uuid4()),
            "email": user.email,
            "hashed_password": hashed_password,
            "full_name": user.full_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        print(f"DEBUG REGISTER: Creating user with data: {user_data}")
        db.create_user(user_data)
        
        print("DEBUG REGISTER: Creating access token...")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        print("DEBUG REGISTER: Registration successful!")
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
        print(f"DEBUG REGISTER: General error: {str(e)}")
        import traceback
        print(f"DEBUG REGISTER: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/login", response_model=UserResponse)
async def login(user: UserLogin):
    """Login user and return access token"""
    try:
        print(f"DEBUG LOGIN: Attempting login for email: {user.email}")
        
        db_user = db.get_user_by_email(user.email)
        print(f"DEBUG LOGIN: Found user: {db_user}")
        
        if not db_user:
            print("DEBUG LOGIN: User not found")
            raise HTTPException(status_code=401, detail="Incorrect email or password")
            
        if not verify_password(user.password, db_user["hashed_password"]):
            print("DEBUG LOGIN: Password verification failed")
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        print("DEBUG LOGIN: Password verified, creating token")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        print(f"DEBUG LOGIN: Token created, returning response")
        
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
        print(f"DEBUG LOGIN: General error: {str(e)}")
        import traceback
        print(f"DEBUG LOGIN: Traceback: {traceback.format_exc()}")
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
        analysis_result = analyze_physique_from_image(file_path)
        
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
        # Get raw request body for debugging
        raw_body = await request.body()
        print(f"DEBUG: Raw request body: {raw_body.decode()}")
        
        # Parse JSON manually to see what we're getting
        import json
        try:
            raw_data = json.loads(raw_body.decode())
            print(f"DEBUG: Parsed raw data: {raw_data}")
        except Exception as parse_error:
            print(f"DEBUG: Failed to parse JSON: {parse_error}")
        
        # Now try to validate with Pydantic
        try:
            user_data = UserData.parse_raw(raw_body)
            print(f"DEBUG: Successfully parsed UserData: {user_data}")
        except ValidationError as ve:
            print(f"DEBUG: Pydantic validation failed: {ve}")
            print(f"DEBUG: Validation errors: {ve.errors()}")
            raise HTTPException(status_code=422, detail=ve.errors())
        
        print(f"DEBUG: user_data.dict(): {user_data.dict()}")
        
        data = user_data.dict()
        data["user_id"] = current_user["id"]
        data["created_at"] = datetime.utcnow().isoformat()
        
        print(f"DEBUG: Final data to store: {data}")
        
        db.store_user_data(current_user["id"], data)
        return {"message": "User data stored successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store user data: {str(e)}")

@app.post("/api/generate-plan", response_model=GeneratedPlan)
async def generate_plan(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate personalized workout and nutrition plan"""
    try:
        # Get raw request body for debugging
        raw_body = await request.body()
        print(f"DEBUG PLAN: Raw request body: {raw_body.decode()}")
        
        # Parse JSON manually to see what we're getting
        import json
        try:
            raw_data = json.loads(raw_body.decode())
            print(f"DEBUG PLAN: Parsed raw data: {raw_data}")
        except Exception as parse_error:
            print(f"DEBUG PLAN: Failed to parse JSON: {parse_error}")
        
        # Now try to validate with Pydantic
        try:
            plan_request = PlanRequest.parse_raw(raw_body)
            print(f"DEBUG PLAN: Successfully parsed PlanRequest: {plan_request}")
        except ValidationError as ve:
            print(f"DEBUG PLAN: Pydantic validation failed: {ve}")
            print(f"DEBUG PLAN: Validation errors: {ve.errors()}")
            raise HTTPException(status_code=422, detail=ve.errors())
        
        # Get user's latest data
        user_data = db.get_latest_user_data(current_user["id"])
        image_analysis = db.get_latest_image_analysis(current_user["id"])
        
        print(f"DEBUG PLAN: User data from DB: {user_data}")
        print(f"DEBUG PLAN: Image analysis from DB: {image_analysis}")
        
        if not user_data:
            raise HTTPException(status_code=400, detail="User data required")
        
        # Generate workout plan
        workout_plan = generate_workout_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            days_per_week=plan_request.days_per_week
        )
        
        print(f"DEBUG PLAN: Generated workout plan: {workout_plan}")
        
        # Generate nutrition plan
        nutrition_plan = generate_nutrition_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            activity_level=plan_request.activity_level
        )
        
        print(f"DEBUG PLAN: Generated nutrition plan: {nutrition_plan}")
        
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
        
        # Try to create the response model
        try:
            result = GeneratedPlan(
                id=plan_data["id"],
                workout_plan=workout_plan,
                nutrition_plan=nutrition_plan,
                rationale="Plan generated based on your physique analysis, goals, and evidence-based fitness principles."
            )
            print(f"DEBUG PLAN: Successfully created GeneratedPlan response: {result}")
            return result
        except ValidationError as ve:
            print(f"DEBUG PLAN: Failed to create GeneratedPlan response: {ve}")
            print(f"DEBUG PLAN: Response validation errors: {ve.errors()}")
            raise HTTPException(status_code=500, detail=f"Response validation failed: {ve.errors()}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG PLAN: General error: {str(e)}")
        import traceback
        print(f"DEBUG PLAN: Traceback: {traceback.format_exc()}")
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

@app.get("/api/debug/users")
async def debug_users():
    """Debug endpoint to check user data structure"""
    try:
        all_users = db.users.all()
        print(f"DEBUG: All users from TinyDB: {all_users}")
        
        # Also check the raw file
        try:
            with open("gym_coach.json", 'r') as f:
                raw_data = json.load(f)
                print(f"DEBUG: Raw database content: {raw_data}")
                return {"tinydb_users": all_users, "raw_data": raw_data}
        except Exception as e:
            print(f"DEBUG: Error reading raw file: {e}")
            return {"tinydb_users": all_users, "error": str(e)}
    except Exception as e:
        print(f"DEBUG: Error in debug endpoint: {e}")
        return {"error": str(e)}

# NEW: Progress tracking endpoints
@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get dashboard data with stats, today's focus, and charts data"""
    try:
        user_id = current_user["id"]
        
        # Get current stats
        latest_user_data = db.get_latest_user_data(user_id)
        weight_logs = db.get_weight_logs(user_id, days=90)
        workout_logs = db.get_workout_logs(user_id, days=30)
        progress_entries = db.get_progress_entries(user_id, days=30)
        latest_plan = db.get_latest_plan(user_id)
        today_progress = db.get_today_progress(user_id)
        weekly_stats = db.get_weekly_workout_stats(user_id)
        
        # Calculate weight changes
        current_weight = weight_logs[-1]["weight"] if weight_logs else (latest_user_data["weight"] if latest_user_data else None)
        weight_change_7d = None
        weight_change_30d = None
        
        if len(weight_logs) >= 2:
            week_ago_weights = [w for w in weight_logs if (datetime.utcnow() - datetime.fromisoformat(w["timestamp"])).days <= 7]
            month_ago_weights = [w for w in weight_logs if (datetime.utcnow() - datetime.fromisoformat(w["timestamp"])).days <= 30]
            
            if week_ago_weights:
                weight_change_7d = current_weight - week_ago_weights[0]["weight"]
            if month_ago_weights:
                weight_change_30d = current_weight - month_ago_weights[0]["weight"]
        
        # Calculate current streak
        current_streak = 0
        today = datetime.utcnow().date()
        for i in range(30):  # Check last 30 days
            check_date = today - timedelta(days=i)
            day_workouts = [w for w in workout_logs if datetime.fromisoformat(w["timestamp"]).date() == check_date]
            if day_workouts:
                current_streak += 1
            else:
                break
        
        # Get next workout
        next_workout = None
        if latest_plan and latest_plan.get("workout_plan"):
            # Simple logic: cycle through workout days
            days_completed = len(workout_logs) % len(latest_plan["workout_plan"])
            if days_completed < len(latest_plan["workout_plan"]):
                next_workout = latest_plan["workout_plan"][days_completed]
        
        stats = DashboardStats(
            current_weight=current_weight,
            weight_change_7d=weight_change_7d,
            weight_change_30d=weight_change_30d,
            workouts_this_week=weekly_stats["completed_workouts"],
            total_workout_time_week=weekly_stats["total_duration_minutes"],
            current_streak=current_streak,
            next_workout=next_workout
        )
        
        # Today's focus
        nutrition_targets = None
        if latest_plan and latest_plan.get("nutrition_plan"):
            nutrition_targets = latest_plan["nutrition_plan"].get("daily_targets")
        
        motivational_messages = [
            "Every workout counts! You're building a stronger you.",
            "Consistency is key - keep up the great work!",
            "Your future self will thank you for today's effort.",
            "Progress, not perfection. Keep moving forward!",
            "Small steps daily lead to big changes yearly."
        ]
        
        todays_focus = TodaysFocus(
            workout_scheduled=next_workout,
            nutrition_targets=nutrition_targets,
            progress_logged=today_progress is not None,
            motivational_message=motivational_messages[len(workout_logs) % len(motivational_messages)]
        )
        
        # Prepare chart data
        recent_progress = [
            {
                "date": entry["timestamp"][:10],
                "energy_level": entry.get("energy_level"),
                "mood": entry.get("mood"),
                "sleep_hours": entry.get("sleep_hours")
            }
            for entry in progress_entries[-14:]  # Last 2 weeks
        ]
        
        weight_trend = [
            {
                "date": log["timestamp"][:10],
                "weight": log["weight"],
                "body_fat": log.get("body_fat_percentage")
            }
            for log in weight_logs[-30:]  # Last 30 entries
        ]
        
        # Workout frequency (last 4 weeks)
        workout_frequency = []
        for week in range(4):
            week_start = datetime.utcnow() - timedelta(weeks=week+1)
            week_end = week_start + timedelta(days=7)
            week_workouts = [
                w for w in workout_logs 
                if week_start <= datetime.fromisoformat(w["timestamp"]) < week_end
            ]
            workout_frequency.append({
                "week": f"Week {4-week}",
                "workouts": len(week_workouts),
                "duration": sum(w.get("duration_minutes", 0) for w in week_workouts)
            })
        
        return DashboardResponse(
            stats=stats,
            todays_focus=todays_focus,
            recent_progress=recent_progress,
            weight_trend=weight_trend,
            workout_frequency=workout_frequency
        )
        
    except Exception as e:
        print(f"DEBUG DASHBOARD: Error: {str(e)}")
        import traceback
        print(f"DEBUG DASHBOARD: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

@app.post("/api/progress")
async def log_progress(
    progress: ProgressEntry,
    current_user: dict = Depends(get_current_user)
):
    """Log daily progress entry"""
    try:
        progress_data = progress.dict()
        db.store_progress_entry(current_user["id"], progress_data)
        return {"message": "Progress logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log progress: {str(e)}")

@app.post("/api/workout-log")
async def log_workout(
    workout: WorkoutLog,
    current_user: dict = Depends(get_current_user)
):
    """Log completed workout"""
    try:
        workout_data = workout.dict()
        db.store_workout_log(current_user["id"], workout_data)
        return {"message": "Workout logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log workout: {str(e)}")

@app.post("/api/weight")
async def log_weight(
    weight: WeightEntry,
    current_user: dict = Depends(get_current_user)
):
    """Log weight entry"""
    try:
        weight_data = weight.dict()
        db.store_weight_entry(current_user["id"], weight_data)
        return {"message": "Weight logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log weight: {str(e)}")

@app.post("/api/measurements")
async def log_measurements(
    measurements: BodyMeasurements,
    current_user: dict = Depends(get_current_user)
):
    """Log body measurements"""
    try:
        measurement_data = measurements.dict()
        db.store_body_measurements(current_user["id"], measurement_data)
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