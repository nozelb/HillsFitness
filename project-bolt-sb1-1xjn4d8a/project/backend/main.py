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
    ImageAnalysisResult, PlanRequest, GeneratedPlan
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
        if db.get_user_by_email(user.email):
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
        if not db_user or not verify_password(user.password, db_user["hashed_password"]):
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
    plan_request: PlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate personalized workout and nutrition plan"""
    try:
        # Get user's latest data
        user_data = db.get_latest_user_data(current_user["id"])
        image_analysis = db.get_latest_image_analysis(current_user["id"])
        
        if not user_data:
            raise HTTPException(status_code=400, detail="User data required")
        
        # Generate workout plan
        workout_plan = generate_workout_plan(
            user_data=user_data,
            image_analysis=image_analysis,
            goal=plan_request.fitness_goal,
            days_per_week=plan_request.days_per_week
        )
        
        # Generate nutrition plan
        nutrition_plan = generate_nutrition_plan(
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
        
        return GeneratedPlan(
            id=plan_data["id"],
            workout_plan=workout_plan,
            nutrition_plan=nutrition_plan,
            rationale="Plan generated based on your physique analysis, goals, and evidence-based fitness principles."
        )
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)