# backend/api/ - Enhanced API endpoints

# api/profile.py - User profile management endpoints
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from database.models import UserProfile, UserMeasurements
from database.database import EnhancedGymDatabase
from services.user_service import UserService
from utils.validators import validate_profile_data, validate_measurements
from .auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])
db = EnhancedGymDatabase()
user_service = UserService(db)

@router.post("/create")
async def create_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create user profile with static data"""
    try:
        # Validate input data
        errors = validate_profile_data(profile_data)
        if errors:
            raise HTTPException(status_code=422, detail=errors)
        
        # Create profile
        profile_id = user_service.create_or_update_profile(current_user["id"], profile_data)
        
        return {
            "message": "Profile created successfully",
            "profile_id": profile_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update")
async def update_profile(
    profile_updates: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # Validate updates
        errors = validate_profile_data(profile_updates)
        if errors:
            raise HTTPException(status_code=422, detail=errors)
        
        # Update profile
        profile_id = user_service.create_or_update_profile(current_user["id"], profile_updates)
        
        return {
            "message": "Profile updated successfully",
            "profile_id": profile_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        profile = user_service.get_profile(current_user["id"])
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/completeness")
async def check_profile_completeness(current_user: dict = Depends(get_current_user)):
    """Check if user profile is complete"""
    try:
        is_complete = user_service.is_profile_complete(current_user["id"])
        latest_measurements = user_service.get_latest_measurements(current_user["id"])
        
        return {
            "profile_complete": is_complete,
            "measurements_available": latest_measurements is not None,
            "can_generate_plan": user_service.can_generate_plan(current_user["id"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/measurements")
async def store_measurements(
    measurement_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Store new measurements (dynamic data)"""
    try:
        # Validate measurements
        errors = validate_measurements(measurement_data)
        if errors:
            raise HTTPException(status_code=422, detail=errors)
        
        # Store measurements
        measurement_id = user_service.store_measurements(current_user["id"], measurement_data)
        
        return {
            "message": "Measurements stored successfully",
            "measurement_id": measurement_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/measurements/latest")
async def get_latest_measurements(current_user: dict = Depends(get_current_user)):
    """Get latest measurements"""
    try:
        measurements = user_service.get_latest_measurements(current_user["id"])
        
        if not measurements:
            raise HTTPException(status_code=404, detail="No measurements found")
        
        return measurements.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/measurements/history")
async def get_measurements_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get measurement history for tracking progress"""
    try:
        measurements = db.get_measurements_history(current_user["id"], limit)
        return [m.dict() for m in measurements]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# api/plans.py - Enhanced plan management endpoints
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from services.plan_service import PlanService
from database.models import CompletePlan, PlanStatus
from .auth import get_current_user

router = APIRouter(prefix="/api/plans", tags=["plans"])
db = EnhancedGymDatabase()
plan_service = PlanService(db)

@router.post("/generate")
async def generate_plan(
    measurement_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Generate a new 4-week plan"""
    try:
        # Check if user can generate plan
        user_service = UserService(db)
        if not user_service.can_generate_plan(current_user["id"]):
            raise HTTPException(
                status_code=400, 
                detail="Complete your profile and measurements first"
            )
        
        # Generate plan
        plan_id = plan_service.generate_plan(current_user["id"], measurement_data)
        
        # Get the generated plan
        plan = db.get_plan_by_id(plan_id)
        
        return {
            "message": "Plan generated successfully",
            "plan_id": plan_id,
            "plan": plan.dict() if plan else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{plan_id}/regenerate")
async def regenerate_plan(
    plan_id: str,
    feedback: str,
    current_user: dict = Depends(get_current_user)
):
    """Regenerate plan with user feedback"""
    try:
        # Verify plan ownership
        original_plan = db.get_plan_by_id(plan_id)
        if not original_plan or original_plan.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Regenerate plan
        new_plan_id = plan_service.regenerate_plan(plan_id, feedback)
        new_plan = db.get_plan_by_id(new_plan_id)
        
        return {
            "message": "Plan regenerated successfully",
            "original_plan_id": plan_id,
            "new_plan_id": new_plan_id,
            "plan": new_plan.dict() if new_plan else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{plan_id}/accept")
async def accept_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Accept and activate a plan"""
    try:
        # Verify plan ownership
        plan = db.get_plan_by_id(plan_id)
        if not plan or plan.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Accept plan
        success = plan_service.accept_plan(plan_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to accept plan")
        
        return {"message": "Plan accepted and activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_plan(current_user: dict = Depends(get_current_user)):
    """Get user's currently active plan"""
    try:
        plan = plan_service.get_active_plan(current_user["id"])
        
        if not plan:
            return {"message": "No active plan found", "plan": None}
        
        return {"plan": plan.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_plan_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get user's plan history"""
    try:
        plans = plan_service.get_plan_history(current_user["id"])
        
        # Convert to summary format for history view
        plan_summaries = []
        for plan in plans[:limit]:
            summary = {
                "id": plan.id,
                "version": plan.version,
                "status": plan.status,
                "created_at": plan.created_at,
                "goal": plan.profile_snapshot.primary_fitness_goal,
                "total_workouts": plan.total_workouts,
                "completion_percentage": 0,  # Calculate based on actual progress
                "parent_plan_id": plan.parent_plan_id
            }
            plan_summaries.append(summary)
        
        return {"plans": plan_summaries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plan_id}")
async def get_plan_details(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed plan information"""
    try:
        plan = db.get_plan_by_id(plan_id)
        
        if not plan or plan.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return {"plan": plan.dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plan_id}/pdf")
async def download_plan_pdf(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download plan as PDF"""
    try:
        plan = db.get_plan_by_id(plan_id)
        
        if not plan or plan.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Generate PDF (implement PDF service)
        from services.pdf_service import PDFService
        pdf_service = PDFService()
        pdf_buffer = pdf_service.generate_plan_pdf(plan)
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=plan_{plan_id}.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# api/dashboard.py - Enhanced dashboard endpoints
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from database.models import ProgressEntry, CheckIn
from services.user_service import UserService
from .auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
db = EnhancedGymDatabase()

@router.get("/")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Get comprehensive dashboard data"""
    try:
        dashboard_data = db.get_dashboard_data(current_user["id"])
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        # Get recent progress and calculate stats
        progress = db.get_progress_history(current_user["id"], days=30)
        measurements = db.get_measurements_history(current_user["id"], limit=10)
        active_plan = db.get_active_plan(current_user["id"])
        
        # Calculate key metrics
        stats = {
            "current_weight": measurements[0].weight_kg if measurements else None,
            "weight_change_30d": None,
            "workouts_this_week": 0,
            "current_streak": 0,
            "plan_progress": 0
        }
        
        # Weight change calculation
        if len(measurements) >= 2:
            recent_weight = measurements[0].weight_kg
            old_weight = measurements[-1].weight_kg
            stats["weight_change_30d"] = recent_weight - old_weight
        
        # Calculate workout frequency and streak
        if progress:
            recent_workouts = [p for p in progress if p.workouts_completed_week and p.workouts_completed_week > 0]
            stats["workouts_this_week"] = len(recent_workouts)
            
            # Calculate streak (simplified)
            stats["current_streak"] = len(progress)
        
        # Plan progress
        if active_plan and active_plan.accepted_at:
            from utils.helpers import calculate_plan_completion_percentage
            import datetime
            start_date = datetime.datetime.fromisoformat(active_plan.accepted_at).date()
            stats["plan_progress"] = calculate_plan_completion_percentage(start_date)
        
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/charts")
async def get_chart_data(current_user: dict = Depends(get_current_user)):
    """Get data for dashboard charts"""
    try:
        chart_data = db._get_chart_data(current_user["id"])
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/progress")
async def log_progress(
    progress_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Log daily progress entry"""
    try:
        progress = ProgressEntry(user_id=current_user["id"], **progress_data)
        progress_id = db.store_progress_entry(progress)
        
        return {
            "message": "Progress logged successfully",
            "progress_id": progress_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/history")
async def get_progress_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get progress history"""
    try:
        progress = db.get_progress_history(current_user["id"], days)
        return {"progress": [p.dict() for p in progress]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/motivation")
async def get_motivational_content(current_user: dict = Depends(get_current_user)):
    """Get personalized motivational content"""
    try:
        from utils.helpers import generate_motivational_message, calculate_next_plan_suggestions
        
        # Get user progress data
        active_plan = db.get_active_plan(current_user["id"])
        progress = db.get_progress_history(current_user["id"], days=7)
        
        progress_data = {
            "completion_percentage": 0,
            "workouts_completed": len(progress),
            "workout_completion_rate": 80  # Would calculate from actual data
        }
        
        if active_plan and active_plan.accepted_at:
            import datetime
            start_date = datetime.datetime.fromisoformat(active_plan.accepted_at).date()
            from utils.helpers import calculate_plan_completion_percentage
            progress_data["completion_percentage"] = calculate_plan_completion_percentage(start_date)
        
        # Generate content
        motivational_message = generate_motivational_message(progress_data)
        next_plan_suggestions = []
        
        if active_plan:
            next_plan_suggestions = calculate_next_plan_suggestions(
                active_plan.dict(), progress_data
            )
        
        return {
            "motivational_message": motivational_message,
            "next_plan_suggestions": next_plan_suggestions,
            "progress_data": progress_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# api/notifications.py - Check-ins and notifications endpoints
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database.models import CheckIn, CheckInType

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
db = EnhancedGymDatabase()

@router.get("/checkins/pending")
async def get_pending_checkins(current_user: dict = Depends(get_current_user)):
    """Get pending check-ins for user"""
    try:
        checkins = db.get_pending_checkins(current_user["id"])
        return {"checkins": [c.dict() for c in checkins]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/checkins/{checkin_id}/complete")
async def complete_checkin(
    checkin_id: str,
    response_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Complete a check-in with response data"""
    try:
        # Verify checkin belongs to user
        CheckInQuery = Query()
        checkin_result = db.check_ins.search(
            (CheckInQuery.id == checkin_id) & (CheckInQuery.user_id == current_user["id"])
        )
        
        if not checkin_result:
            raise HTTPException(status_code=404, detail="Check-in not found")
        
        # Complete the check-in
        success = db.complete_checkin(checkin_id, response_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete check-in")
        
        return {"message": "Check-in completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/checkins/history")
async def get_checkin_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get check-in history"""
    try:
        CheckInQuery = Query()
        checkins = db.check_ins.search(CheckInQuery.user_id == current_user["id"])
        
        # Sort by created_at and limit
        sorted_checkins = sorted(checkins, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]
        
        return {"checkins": sorted_checkins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/checkins/create")
async def create_custom_checkin(
    checkin_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a custom check-in reminder"""
    try:
        checkin = CheckIn(user_id=current_user["id"], **checkin_data)
        checkin_id = db.store_checkin(checkin)
        
        return {
            "message": "Check-in created successfully",
            "checkin_id": checkin_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# services/pdf_service.py - PDF generation service
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from typing import Dict, Any
from database.models import CompletePlan

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2563eb')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#1f2937')
        ))
        
        self.styles.add(ParagraphStyle(
            name='WorkoutDay',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#059669')
        ))
    
    def generate_plan_pdf(self, plan: CompletePlan) -> bytes:
        """Generate PDF for a complete plan"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        story = []
        
        # Title page
        self._add_title_page(story, plan)
        story.append(PageBreak())
        
        # Plan overview
        self._add_plan_overview(story, plan)
        story.append(PageBreak())
        
        # 4-week workout plan
        self._add_workout_plan(story, plan)
        story.append(PageBreak())
        
        # Nutrition plan
        self._add_nutrition_plan(story, plan)
        story.append(PageBreak())
        
        # Progress tracking section
        self._add_progress_tracking(story, plan)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _add_title_page(self, story, plan: CompletePlan):
        """Add title page to PDF"""
        story.append(Spacer(1, 2*inch))
        
        title = Paragraph("4-Week Personalized Training & Nutrition Plan", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # User info
        user_info = f"""
        <b>Name:</b> {plan.profile_snapshot.full_name}<br/>
        <b>Goal:</b> {plan.profile_snapshot.primary_fitness_goal.value.replace('_', ' ').title()}<br/>
        <b>Training Days:</b> {plan.profile_snapshot.preferred_training_days} days per week<br/>
        <b>Experience Level:</b> {plan.profile_snapshot.gym_experience.value.title()}<br/>
        <b>Plan Created:</b> {plan.created_at.strftime('%B %d, %Y')}
        """
        
        user_para = Paragraph(user_info, self.styles['Normal'])
        story.append(user_para)
        story.append(Spacer(1, 1*inch))
        
        # Important notes
        notes = """
        <b>Important Notes:</b><br/>
        • Follow the plan for 4 consecutive weeks<br/>
        • Rest 1-2 days between workouts<br/>
        • Focus on proper form over heavy weights<br/>
        • Stay hydrated and get adequate sleep<br/>
        • Consult a healthcare provider before starting any new exercise program
        """
        
        notes_para = Paragraph(notes, self.styles['Normal'])
        story.append(notes_para)
    
    def _add_plan_overview(self, story, plan: CompletePlan):
        """Add plan overview section"""
        story.append(Paragraph("Plan Overview", self.styles['SectionHeader']))
        
        # Overview table
        overview_data = [
            ['Total Workouts', str(plan.total_workouts)],
            ['Estimated Time per Week', f"{plan.estimated_time_per_week} minutes"],
            ['Plan Duration', '4 weeks'],
            ['Training Style', 'Progressive overload with variety'],
            ['Equipment Needed', 'Basic gym equipment']
        ]
        
        overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Safety checks
        if plan.safety_checks:
            story.append(Paragraph("Safety Validation", self.styles['SectionHeader']))
            
            safety_text = "<b>✓ All safety requirements met</b><br/>"
            safety_text += "• Minimum calorie requirements satisfied<br/>"
            safety_text += "• Protein intake adequate for goals<br/>"
            safety_text += "• Training frequency appropriate for experience level<br/>"
            safety_text += "• Progressive overload within safe limits"
            
            safety_para = Paragraph(safety_text, self.styles['Normal'])
            story.append(safety_para)
    
    def _add_workout_plan(self, story, plan: CompletePlan):
        """Add 4-week workout plan"""
        story.append(Paragraph("4-Week Workout Plan", self.styles['SectionHeader']))
        
        for week in plan.workout_weeks:
            # Week header
            week_title = f"Week {week.week_number}: {week.focus}"
            story.append(Paragraph(week_title, self.styles['WorkoutDay']))
            
            # Week notes
            if week.notes:
                notes_para = Paragraph(f"<i>{week.notes}</i>", self.styles['Normal'])
                story.append(notes_para)
                story.append(Spacer(1, 0.1*inch))
            
            # Workouts for this week
            for workout in week.workouts:
                # Workout day header
                day_header = f"{workout.day_name} - {', '.join(workout.muscle_groups).title()}"
                story.append(Paragraph(day_header, self.styles['Heading4']))
                
                # Exercise table
                exercise_data = [['Exercise', 'Sets', 'Reps', 'Rest', 'Notes']]
                
                for exercise in workout.exercises:
                    exercise_data.append([
                        exercise.name,
                        str(exercise.sets),
                        exercise.reps,
                        f"{exercise.rest_seconds}s",
                        exercise.notes[:30] + "..." if exercise.notes and len(exercise.notes) > 30 else exercise.notes or ""
                    ])
                
                exercise_table = Table(exercise_data, colWidths=[2.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 2*inch])
                exercise_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.gray)
                ]))
                
                story.append(exercise_table)
                story.append(Spacer(1, 0.2*inch))
            
            if week.week_number < 4:  # Don't add page break after last week
                story.append(PageBreak())
    
    def _add_nutrition_plan(self, story, plan: CompletePlan):
        """Add nutrition plan section"""
        story.append(Paragraph("Nutrition Plan", self.styles['SectionHeader']))
        
        # Daily targets
        targets = plan.nutrition_plan.daily_targets
        targets_data = [
            ['Nutrient', 'Daily Target'],
            ['Calories', f"{targets.calories} kcal"],
            ['Protein', f"{targets.protein_g}g"],
            ['Carbohydrates', f"{targets.carbs_g}g"],
            ['Fat', f"{targets.fat_g}g"],
            ['Fiber', f"{targets.fiber_g}g"],
            ['Water', f"{targets.water_ml}ml"]
        ]
        
        targets_table = Table(targets_data, colWidths=[2*inch, 2*inch])
        targets_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcfce7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(targets_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Sample meals
        story.append(Paragraph("Sample Daily Meal Plan", self.styles['WorkoutDay']))
        
        for meal in plan.nutrition_plan.meal_plan:
            meal_header = f"{meal.meal_type.title()}: {meal.name}"
            story.append(Paragraph(meal_header, self.styles['Heading4']))
            
            meal_info = f"""
            <b>Calories:</b> {meal.calories} | <b>Protein:</b> {meal.protein_g}g | 
            <b>Carbs:</b> {meal.carbs_g}g | <b>Fat:</b> {meal.fat_g}g<br/>
            <b>Ingredients:</b> {', '.join(meal.ingredients)}
            """
            
            if meal.prep_time_minutes:
                meal_info += f"<br/><b>Prep Time:</b> {meal.prep_time_minutes} minutes"
            
            meal_para = Paragraph(meal_info, self.styles['Normal'])
            story.append(meal_para)
            story.append(Spacer(1, 0.15*inch))
        
        # Nutrition tips
        if plan.nutrition_plan.nutrition_tips:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Nutrition Tips", self.styles['WorkoutDay']))
            
            tips_text = ""
            for tip in plan.nutrition_plan.nutrition_tips:
                tips_text += f"• {tip}<br/>"
            
            tips_para = Paragraph(tips_text, self.styles['Normal'])
            story.append(tips_para)
    
    def _add_progress_tracking(self, story, plan: CompletePlan):
        """Add progress tracking section"""
        story.append(Paragraph("Progress Tracking", self.styles['SectionHeader']))
        
        # Weekly weight log
        story.append(Paragraph("Weekly Weight Log", self.styles['WorkoutDay']))
        
        weight_data = [['Week', 'Date', 'Weight (kg)', 'Body Fat %', 'Notes']]
        for i in range(1, 5):
            weight_data.append([f'Week {i}', '', '', '', ''])
        
        weight_table = Table(weight_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.5*inch, 2*inch])
        weight_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        story.append(weight_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Workout completion log
        story.append(Paragraph("Workout Completion Log", self.styles['WorkoutDay']))
        
        completion_text = """
        Use this section to track your workout completion:<br/><br/>
        
        Week 1: ☐ Day 1  ☐ Day 2  ☐ Day 3  ☐ Day 4<br/>
        Week 2: ☐ Day 1  ☐ Day 2  ☐ Day 3  ☐ Day 4<br/>
        Week 3: ☐ Day 1  ☐ Day 2  ☐ Day 3  ☐ Day 4<br/>
        Week 4: ☐ Day 1  ☐ Day 2  ☐ Day 3  ☐ Day 4<br/><br/>
        
        <b>Notes Section:</b><br/>
        Use this space to record how you felt during workouts, any modifications made,
        or observations about your progress.
        """
        
        completion_para = Paragraph(completion_text, self.styles['Normal'])
        story.append(completion_para)
