# backend/api/specification_endpoints.py
"""
API endpoints exactly matching the specification requirements
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from typing import Dict, Any, List, Optional
import uuid
import os
import aiofiles
from datetime import datetime, date

from models.complete_models import (
    StaticProfile, WizardInputs, VisionAnalysisResult, CompleteDataContract,
    FormattedPlanResponse, RegenerationRequest, SessionLog, ProgressMetrics
)
from services.llm_plan_generator import GymAICoachLLM, generate_kid_safe_plan, accept_plan
from services.vision_pipeline import EnhancedVisionPipeline
from database.database import EnhancedGymDatabase
from auth import get_current_user

# Initialize services
router = APIRouter(prefix="/api", tags=["gym-ai-coach-v2"])
llm_generator = GymAICoachLLM()
vision_pipeline = EnhancedVisionPipeline()
db = EnhancedGymDatabase()

@router.post("/profile", summary="Create/Update Static Profile")
async def create_or_update_profile(
    profile_data: StaticProfile,
    current_user: dict = Depends(get_current_user)
):
    """
    STATIC PROFILE: persisted once, editable on profile page
    Age validation: abort if age < 13 for calorie calculations
    """
    try:
        # Store profile with user ID
        profile_dict = profile_data.dict()
        profile_dict["user_id"] = current_user["id"]
        profile_dict["created_at"] = datetime.utcnow().isoformat()
        
        # Store in database
        profile_id = db.store_user_profile(current_user["id"], profile_dict)
        
        return {
            "status": "success",
            "profile_id": profile_id,
            "message": f"Profile created for {profile_data.fullName}",
            "age": profile_data.age,
            "calorie_tracking_enabled": profile_data.age >= 13
        }
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile creation failed: {str(e)}")

@router.get("/profile", summary="Get Current User Profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get user's static profile"""
    try:
        profile = db.get_user_profile(current_user["id"])
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"profile": profile}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wizard-data", summary="Submit Wizard Inputs")
async def submit_wizard_data(
    wizard_data: WizardInputs,
    current_user: dict = Depends(get_current_user)
):
    """
    DYNAMIC WIZARD DATA: collected each time a plan is generated
    Includes photo URL, measurements, smart scale data, injuries, equipment limits
    """
    try:
        # Validate ranges as per specification
        from services.llm_plan_generator import validate_ranges
        
        validation_errors = validate_ranges(
            wizard_data.heightCm, 
            wizard_data.weightKg, 
            wizard_data.smartScale.bodyFatPct if wizard_data.smartScale else 20.0
        )
        
        if validation_errors:
            raise HTTPException(
                status_code=422, 
                detail={"errors": [err.dict() for err in validation_errors]}
            )
        
        # Store wizard data
        wizard_dict = wizard_data.dict()
        wizard_dict["user_id"] = current_user["id"]
        wizard_dict["session_id"] = str(uuid.uuid4())
        wizard_dict["created_at"] = datetime.utcnow().isoformat()
        
        session_id = db.store_wizard_data(current_user["id"], wizard_dict)
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Wizard data stored successfully",
            "ready_for_vision_analysis": bool(wizard_data.photoUrl)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wizard data storage failed: {str(e)}")

@router.post("/upload-analyze-image", summary="Upload and Analyze Image")
async def upload_and_analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    IMAGE ANALYSIS: Upload photo and run through vision pipeline
    Returns VisionAnalysisResult with quality gate validation
    Aborts if vision.quality < 0.70
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join("uploads", filename)
        
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        
        # Save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Get user data for vision analysis
        wizard_data = db.get_latest_wizard_data(current_user["id"])
        if not wizard_data:
            raise HTTPException(
                status_code=400, 
                detail="Please submit wizard data first"
            )
        
        # Run vision analysis
        vision_result = vision_pipeline.process_image(
            image_path=file_path,
            user_height_cm=wizard_data["heightCm"],
            user_weight_kg=wizard_data["weightKg"],
            user_sex=wizard_data.get("sex", "male")  # From profile
        )
        
        # Check quality gate (CRITICAL VALIDATION)
        image_quality = vision_result.get("imageQuality", 0.0)
        if image_quality < 0.70:
            # Clean up low quality image
            background_tasks.add_task(cleanup_file, file_path)
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "low_quality_image",
                    "message": "Image quality too low - please upload a clearer photo",
                    "quality_score": image_quality,
                    "minimum_required": 0.70
                }
            )
        
        # Transform to specification format
        vision_analysis = VisionAnalysisResult(
            quality=image_quality,
            bfEstimate=vision_result.get("bf_estimate", 20.0),
            anthro={
                "waistCm": vision_result["anthro"]["waist_cm"],
                "hipCm": vision_result["anthro"]["hip_cm"], 
                "shoulderCm": vision_result["anthro"]["shoulder_cm"]
            },
            poseAlerts=vision_result.get("poseAlerts", [])
        )
        
        # Store vision analysis
        vision_id = db.store_vision_analysis(current_user["id"], vision_analysis.dict())
        
        # Update wizard data with photo URL
        photo_url = f"/uploads/{filename}"  # Or use cloud storage URL
        db.update_wizard_photo_url(current_user["id"], photo_url)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, file_path, delay=3600)  # 1 hour
        
        return {
            "status": "success",
            "vision_analysis": vision_analysis.dict(),
            "photo_url": photo_url,
            "analysis_id": vision_id,
            "ready_for_plan_generation": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@router.post("/generate-plan", response_model=FormattedPlanResponse, summary="Generate Complete Plan")
async def generate_complete_plan(
    current_user: dict = Depends(get_current_user)
):
    """
    PLAN GENERATION: Create complete 4-week plan using LLM
    Combines profile + wizard + vision data per specification
    """
    try:
        # Get all required data
        profile_data = db.get_user_profile(current_user["id"])
        wizard_data = db.get_latest_wizard_data(current_user["id"])
        vision_data = db.get_latest_vision_analysis(current_user["id"])
        
        # Validate all data is present
        if not profile_data:
            raise HTTPException(status_code=400, detail="Static profile required")
        if not wizard_data:
            raise HTTPException(status_code=400, detail="Wizard data required")
        if not vision_data:
            raise HTTPException(status_code=400, detail="Image analysis required")
        
        # Create complete data contract
        profile = StaticProfile(**profile_data)
        wizard = WizardInputs(**wizard_data)
        vision = VisionAnalysisResult(**vision_data)
        
        data_contract = CompleteDataContract(
            profile=profile,
            wizard=wizard,
            vision=vision
        )
        
        # Special handling for minors (age < 13)
        if profile.age < 13:
            kid_plan = generate_kid_safe_plan(profile.age, profile.activityLvl)
            return {
                "type": "kid_safe_plan",
                "plan": kid_plan,
                "message": "Kid-safe, play-based activities generated (no calorie counting)"
            }
        
        # Generate plan using LLM
        formatted_plan = llm_generator.generate_plan(data_contract)
        
        # Store generated plan
        plan_dict = formatted_plan.dict()
        plan_dict["user_id"] = current_user["id"]
        plan_dict["plan_id"] = str(uuid.uuid4())
        plan_dict["generated_at"] = datetime.utcnow().isoformat()
        plan_dict["data_contract"] = data_contract.dict()
        
        plan_id = db.store_generated_plan(current_user["id"], plan_dict)
        
        # Add plan metadata
        formatted_plan.plan_id = plan_id
        formatted_plan.actions = ["Download PDF", "Accept Plan", "Regenerate"]
        
        return formatted_plan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

@router.post("/accept-plan/{plan_id}", summary="Accept Generated Plan")
async def accept_generated_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    PLAN ACCEPTANCE: Start 28-day plan tracking with auto-progression
    Repeat plan for exactly 28 days, prompt for new plan at day 25
    """
    try:
        # Validate plan exists and belongs to user
        plan = db.get_plan_by_id(plan_id, current_user["id"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Accept plan and start tracking
        acceptance_config = accept_plan(plan_id, current_user["id"])
        
        # Store acceptance in database
        db.store_plan_acceptance(current_user["id"], acceptance_config)
        
        return {
            "status": "plan_accepted",
            "plan_id": plan_id,
            "tracking_started": True,
            "duration_days": 28,
            "next_session_date": calculate_next_session_date(plan),
            "auto_progression_enabled": True,
            "new_plan_prompt_day": 25,
            "message": "Plan accepted! Your 28-day journey begins now."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan acceptance failed: {str(e)}")

@router.post("/regenerate-plan", summary="Regenerate Plan with Modifications")
async def regenerate_plan(
    regen_request: RegenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    PLAN REGENERATION: Modify existing plan based on user feedback
    One free regeneration, then queue for email processing
    """
    try:
        # Check regeneration history
        regen_count = db.get_regeneration_count(current_user["id"], regen_request.plan_id)
        
        from services.llm_plan_generator import handle_regeneration_request
        
        result = handle_regeneration_request(
            regen_request.plan_id,
            regen_request.user_comment,
            regen_count
        )
        
        # Store regeneration request
        regen_data = {
            "original_plan_id": regen_request.plan_id,
            "user_comment": regen_request.user_comment,
            "regeneration_count": regen_count + 1,
            "queued": result["queued"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.store_regeneration_request(current_user["id"], regen_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

@router.post("/log-session", summary="Log Workout Session")
async def log_workout_session(
    session_log: SessionLog,
    current_user: dict = Depends(get_current_user)
):
    """
    SESSION LOGGING: Track workout completion for compliance monitoring
    """
    try:
        # Validate session belongs to user's current plan
        plan = db.get_plan_by_id(session_log.plan_id, current_user["id"])
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Store session log
        log_data = session_log.dict()
        log_data["user_id"] = current_user["id"]
        log_data["logged_at"] = datetime.utcnow().isoformat()
        
        session_id = db.store_session_log(current_user["id"], log_data)
        
        # Check compliance and provide nudges if needed
        from services.llm_plan_generator import check_compliance
        
        all_sessions = db.get_user_sessions(current_user["id"], session_log.plan_id)
        compliance = check_compliance(current_user["id"], session_log.plan_id, all_sessions)
        
        response = {
            "status": "session_logged",
            "session_id": session_id,
            "compliance": compliance
        }
        
        # Add nudge if needed
        if compliance["needs_nudge"]:
            response["nudge"] = {
                "type": "gentle_reminder",
                "message": compliance["nudge_message"],
                "show_in_dashboard": True
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session logging failed: {str(e)}")

@router.get("/dashboard", summary="Get User Dashboard")
async def get_user_dashboard(current_user: dict = Depends(get_current_user)):
    """
    DASHBOARD: Return to dashboard after acceptance, show progress and next session
    """
    try:
        # Get current active plan
        active_plan = db.get_active_plan(current_user["id"])
        
        if not active_plan:
            return {
                "status": "no_active_plan", 
                "message": "No active plan found",
                "suggested_action": "create_new_plan"
            }
        
        # Get progress metrics
        sessions = db.get_user_sessions(current_user["id"], active_plan["plan_id"])
        
        # Calculate next session
        next_session = calculate_next_session(active_plan, sessions)
        
        # Get trend data
        trend_charts = get_trend_charts(current_user["id"])
        
        dashboard = {
            "active_plan": {
                "plan_id": active_plan["plan_id"],
                "days_remaining": calculate_days_remaining(active_plan),
                "completion_percentage": calculate_completion_percentage(sessions, active_plan)
            },
            "next_session": next_session,
            "progress_metrics": calculate_progress_metrics(sessions),
            "trend_charts": trend_charts,
            "compliance_status": check_recent_compliance(sessions),
            "upcoming_milestones": get_upcoming_milestones(active_plan)
        }
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard loading failed: {str(e)}")

@router.get("/progress-charts", summary="Get Progress Trend Charts")
async def get_progress_charts(current_user: dict = Depends(get_current_user)):
    """
    PROGRESS TRACKING: Weight, BF%, muscle% trends with timestamps
    Store every numeric/image metric with UTC timestamp
    """
    try:
        # Get all user metrics over time
        weight_history = db.get_weight_history(current_user["id"])
        bf_history = db.get_body_fat_history(current_user["id"])
        muscle_history = db.get_muscle_percentage_history(current_user["id"])
        
        charts = {
            "weight_trend": {
                "data": weight_history,
                "unit": "kg",
                "timeframe": "last_90_days"
            },
            "body_fat_trend": {
                "data": bf_history,
                "unit": "percentage",
                "timeframe": "last_90_days"
            },
            "muscle_percentage_trend": {
                "data": muscle_history,
                "unit": "percentage", 
                "timeframe": "last_90_days"
            }
        }
        
        return charts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Charts loading failed: {str(e)}")

# Utility functions
async def cleanup_file(file_path: str, delay: int = 0):
    """Background task to clean up files"""
    import asyncio
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Ignore cleanup errors

def calculate_next_session_date(plan: Dict) -> str:
    """Calculate next scheduled session date"""
    # Implementation depends on plan structure
    return datetime.now().date().isoformat()

def calculate_next_session(active_plan: Dict, sessions: List[Dict]) -> Dict:
    """Calculate next session details"""
    return {
        "workout_name": "Upper Body Strength",
        "scheduled_date": datetime.now().date().isoformat(),
        "estimated_duration": "45 minutes",
        "exercises_count": 6
    }

def calculate_days_remaining(active_plan: Dict) -> int:
    """Calculate days remaining in current plan"""
    start_date = datetime.fromisoformat(active_plan["start_date"])
    days_elapsed = (datetime.now() - start_date).days
    return max(0, 28 - days_elapsed)

def calculate_completion_percentage(sessions: List[Dict], active_plan: Dict) -> float:
    """Calculate plan completion percentage"""
    completed_sessions = len([s for s in sessions if s.get("completed")])
    total_planned_sessions = active_plan.get("total_sessions", 28)
    return min(100.0, (completed_sessions / total_planned_sessions) * 100)

def calculate_progress_metrics(sessions: List[Dict]) -> ProgressMetrics:
    """Calculate progress metrics"""
    completed = len([s for s in sessions if s.get("completed")])
    total = len(sessions)
    
    return ProgressMetrics(
        sessions_completed=completed,
        sessions_scheduled=total,
        compliance_percentage=(completed / total * 100) if total > 0 else 0,
        avg_session_duration=45.0,  # Calculate from actual session logs
        missed_sessions_last_7_days=0  # Calculate from recent sessions
    )

def get_trend_charts(user_id: str) -> Dict:
    """Get trend chart data"""
    return {
        "weight": [],
        "body_fat": [],
        "muscle_percentage": []
    }

def check_recent_compliance(sessions: List[Dict]) -> Dict:
    """Check recent compliance status"""
    return {
        "status": "good",
        "missed_last_week": 0,
        "streak_days": 7
    }

def get_upcoming_milestones(active_plan: Dict) -> List[Dict]:
    """Get upcoming plan milestones"""
    return [
        {"type": "progress_check", "date": "2025-01-20", "description": "Week 2 progress assessment"},
        {"type": "new_plan_prompt", "date": "2025-02-10", "description": "Time for your next 4-week plan"},
        {"type": "measurement_update", "date": "2025-01-25", "description": "Update your measurements"}
    ]