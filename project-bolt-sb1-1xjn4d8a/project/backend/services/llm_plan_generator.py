# backend/services/llm_plan_generator.py
"""
LLM Plan Generator following the exact specification format
Transforms data contract into specification-compliant plans
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from models.complete_models import (
    CompleteDataContract, FormattedPlanResponse, PlanOverview, 
    WeeklyNutritionTable, TrainingTable, SafetyCheck, ValidationError
)

logger = logging.getLogger(__name__)

class GymAICoachLLM:
    """
    LLM-based plan generator that follows the exact specification:
    - Professional, clinical tone (no marketing fluff)
    - Metric units only (kg, cm, kJ, g, mL)
    - 4-week mesocycle structure
    - Evidence-based recommendations
    """
    
    def __init__(self):
        self.version = "2.1.0"
        self.legal_disclaimer = (
            "Information is for educational purposes only and is not a substitute "
            "for professional medical advice. Consult a healthcare provider before "
            "starting any exercise or nutrition program."
        )
    
    def generate_plan(self, data_contract: CompleteDataContract) -> FormattedPlanResponse:
        """
        Main entry point - generates complete plan from data contract
        Following the exact specification format
        """
        try:
            # Validate inputs first
            safety_check = self._validate_safety(data_contract)
            if not safety_check.is_safe:
                raise ValueError(f"Safety validation failed: {safety_check.warnings}")
            
            # Extract key data
            profile = data_contract.profile
            wizard = data_contract.wizard
            vision = data_contract.vision
            
            # Calculate nutritional targets
            nutrition_targets = self._calculate_nutrition_targets(profile, wizard, vision)
            
            # Generate workout plan with vision adjustments
            training_plan = self._generate_training_plan(profile, wizard, vision)
            
            # Create meal suggestions
            meal_ideas = self._generate_meal_ideas(nutrition_targets, profile)
            
            # Generate corrective exercises based on posture alerts
            mobility_drills = self._generate_mobility_drills(vision.poseAlerts)
            
            # Create rationale with user data references
            rationale = self._generate_rationale(profile, wizard, vision)
            
            # Format according to specification
            formatted_response = self._format_response(
                profile, nutrition_targets, training_plan, 
                meal_ideas, mobility_drills, rationale
            )
            
            logger.info(f"Plan generated successfully for user {profile.fullName}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Plan generation failed: {str(e)}")
            raise
    
    def _validate_safety(self, data_contract: CompleteDataContract) -> SafetyCheck:
        """Hard validation rules from specification"""
        warnings = []
        blocked_exercises = []
        
        profile = data_contract.profile
        wizard = data_contract.wizard
        vision = data_contract.vision
        
        # Age validation
        if profile.age < 13:
            return SafetyCheck(
                is_safe=False,
                warnings=["User under 13 - no calorie counting, kid-safe workouts only"]
            )
        
        # Range validation
        if not (100 <= wizard.heightCm <= 230):
            warnings.append(f"Height {wizard.heightCm}cm outside normal range")
        
        if not (30 <= wizard.weightKg <= 300):
            warnings.append(f"Weight {wizard.weightKg}kg outside normal range")
        
        if not (3 <= vision.bfEstimate <= 60):
            warnings.append(f"Body fat {vision.bfEstimate}% outside normal range")
        
        # Image quality gate
        if vision.quality < 0.70:
            return SafetyCheck(
                is_safe=False,
                warnings=["Image quality too low - request clearer photo"]
            )
        
        # Injury-based exercise restrictions
        for injury in wizard.injuries:
            if "knee" in injury.lower():
                blocked_exercises.extend(["lunges", "jump squats", "plyometrics"])
            if "shoulder" in injury.lower():
                blocked_exercises.extend(["overhead press", "pull-ups"])
            if "back" in injury.lower():
                blocked_exercises.extend(["deadlifts", "bent-over rows"])
        
        return SafetyCheck(
            is_safe=len(warnings) == 0,
            warnings=warnings,
            blocked_exercises=blocked_exercises
        )
    
    def _calculate_nutrition_targets(self, profile, wizard, vision) -> List[WeeklyNutritionTable]:
        """Calculate TDEE and macro targets using Mifflin-St Jeor (metric)"""
        
        # Mifflin-St Jeor equation (metric)
        if profile.sex == "male":
            bmr = 10 * wizard.weightKg + 6.25 * wizard.heightCm - 5 * profile.age + 5
        else:
            bmr = 10 * wizard.weightKg + 6.25 * wizard.heightCm - 5 * profile.age - 161
        
        # Activity multipliers
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "high": 1.725
        }
        
        tdee = bmr * activity_multipliers[profile.activityLvl]
        
        # Goal-based calorie adjustments
        calorie_adjustments = {
            "fat-loss": 0.85,      # TDEE × 0.85
            "muscle-gain": 1.10,   # TDEE × 1.10
            "recomp": 1.00,        # TDEE × 1.00
            "maintenance": 1.00    # TDEE × 1.00
        }
        
        target_calories = tdee * calorie_adjustments[profile.primaryGoal]
        
        # Convert to kilojoules (1 kcal = 4.184 kJ)
        target_kj = int(target_calories * 4.184)
        
        # Default macro percentages (adjustable ±5% for allergies)
        protein_pct = 0.30  # 30% of kJ
        carb_pct = 0.45     # 45% of kJ
        fat_pct = 0.25      # 25% of kJ
        
        # Vision-based adjustments
        if vision.bfEstimate > 25:
            # Higher body fat - increase protein slightly
            protein_pct = 0.35
            carb_pct = 0.40
        elif vision.bfEstimate < 12:
            # Very lean - maintain/increase carbs
            carb_pct = 0.50
            protein_pct = 0.25
        
        # Calculate macros in grams
        protein_g = int((target_kj * protein_pct / 4.184) / 4)  # 4 kcal per g protein
        carb_g = int((target_kj * carb_pct / 4.184) / 4)        # 4 kcal per g carb
        fat_g = int((target_kj * fat_pct / 4.184) / 9)          # 9 kcal per g fat
        
        # Same targets for all 4 weeks (can be customized for periodization)
        return [
            WeeklyNutritionTable(
                week="1-4",
                kJ_per_day=target_kj,
                protein_g=protein_g,
                carbs_g=carb_g,
                fat_g=fat_g
            )
        ]
    
    def _generate_training_plan(self, profile, wizard, vision) -> List[TrainingTable]:
        """Generate 4-week training mesocycle with vision adjustments"""
        
        training_plan = []
        
        # Corrective exercises first (based on pose alerts)
        corrective_exercises = self._get_corrective_exercises(vision.poseAlerts)
        for exercise in corrective_exercises:
            training_plan.append(TrainingTable(
                day="Daily",
                exercise=exercise["name"],
                sets=exercise["sets"],
                reps=exercise["reps"],
                rest=exercise["rest"]
            ))
        
        # Main training plan based on training days
        if profile.trainDays >= 4:
            # Full body split
            main_exercises = [
                {"day": "Day 1", "exercise": "Goblet Squat", "sets": 4, "reps": "8-10", "rest": "90 s"},
                {"day": "Day 1", "exercise": "Push-ups", "sets": 3, "reps": "8-12", "rest": "60 s"},
                {"day": "Day 1", "exercise": "Bent-over Row", "sets": 3, "reps": "8-12", "rest": "90 s"},
                
                {"day": "Day 2", "exercise": "Romanian Deadlift", "sets": 4, "reps": "6-8", "rest": "120 s"},
                {"day": "Day 2", "exercise": "Overhead Press", "sets": 3, "reps": "8-10", "rest": "90 s"},
                {"day": "Day 2", "exercise": "Plank", "sets": 3, "reps": "30-60 s", "rest": "60 s"},
                
                {"day": "Day 3", "exercise": "Bulgarian Split Squat", "sets": 3, "reps": "8-10", "rest": "90 s"},
                {"day": "Day 3", "exercise": "Pull-ups/Lat Pulldown", "sets": 3, "reps": "6-10", "rest": "90 s"},
                {"day": "Day 3", "exercise": "Dips/Tricep Press", "sets": 3, "reps": "8-12", "rest": "60 s"},
                
                {"day": "Day 4", "exercise": "Front Squat", "sets": 4, "reps": "6-8", "rest": "120 s"},
                {"day": "Day 4", "exercise": "Incline Push-ups", "sets": 3, "reps": "10-15", "rest": "60 s"},
                {"day": "Day 4", "exercise": "Face Pulls", "sets": 3, "reps": "12-15", "rest": "45 s"},
            ]
        else:
            # 3-day full body
            main_exercises = [
                {"day": "Day 1", "exercise": "Squat", "sets": 3, "reps": "8-12", "rest": "90 s"},
                {"day": "Day 1", "exercise": "Push-ups", "sets": 3, "reps": "8-15", "rest": "60 s"},
                {"day": "Day 1", "exercise": "Bent-over Row", "sets": 3, "reps": "8-12", "rest": "90 s"},
                
                {"day": "Day 2", "exercise": "Deadlift", "sets": 3, "reps": "6-8", "rest": "120 s"},
                {"day": "Day 2", "exercise": "Overhead Press", "sets": 3, "reps": "8-10", "rest": "90 s"},
                {"day": "Day 2", "exercise": "Plank", "sets": 2, "reps": "30-45 s", "rest": "60 s"},
                
                {"day": "Day 3", "exercise": "Lunge", "sets": 3, "reps": "8-10", "rest": "60 s"},
                {"day": "Day 3", "exercise": "Pull-ups", "sets": 3, "reps": "6-10", "rest": "90 s"},
                {"day": "Day 3", "exercise": "Dips", "sets": 3, "reps": "8-12", "rest": "60 s"},
            ]
        
        # Apply equipment limitations
        if "no barbell" in wizard.equipLimits:
            for exercise in main_exercises:
                if "Deadlift" in exercise["exercise"]:
                    exercise["exercise"] = "Romanian Deadlift (Dumbbells)"
                elif "Squat" in exercise["exercise"] and "Goblet" not in exercise["exercise"]:
                    exercise["exercise"] = "Goblet Squat"
        
        # Apply injury modifications
        for injury in wizard.injuries:
            if "knee" in injury.lower():
                for exercise in main_exercises:
                    if "Lunge" in exercise["exercise"]:
                        exercise["exercise"] = "Leg Press"
                        exercise["reps"] = "12-15"
        
        # Convert to TrainingTable format
        for exercise in main_exercises:
            training_plan.append(TrainingTable(
                day=exercise["day"],
                exercise=exercise["exercise"],
                sets=exercise["sets"],
                reps=exercise["reps"],
                rest=exercise["rest"]
            ))
        
        return training_plan
    
    def _get_corrective_exercises(self, pose_alerts: List[str]) -> List[Dict]:
        """Generate corrective exercises for posture issues"""
        corrective_exercises = []
        
        if "rounded_shoulders" in pose_alerts:
            corrective_exercises.extend([
                {"name": "Wall Angels", "sets": 3, "reps": "15", "rest": "30 s"},
                {"name": "Doorway Chest Stretch", "sets": 3, "reps": "30 s", "rest": "30 s"},
                {"name": "Face Pulls", "sets": 3, "reps": "15", "rest": "60 s"}
            ])
        
        if "anterior_pelvic_tilt" in pose_alerts:
            corrective_exercises.extend([
                {"name": "Hip Flexor Stretch", "sets": 2, "reps": "60 s", "rest": "30 s"},
                {"name": "Dead Bug", "sets": 2, "reps": "8 each side", "rest": "45 s"},
                {"name": "Glute Bridge", "sets": 3, "reps": "12-15", "rest": "60 s"}
            ])
        
        if "forward_head" in pose_alerts:
            corrective_exercises.extend([
                {"name": "Chin Tucks", "sets": 3, "reps": "10", "rest": "30 s"},
                {"name": "Upper Trap Stretch", "sets": 2, "reps": "30 s each", "rest": "30 s"}
            ])
        
        return corrective_exercises
    
    def _generate_meal_ideas(self, nutrition_targets: List[WeeklyNutritionTable], profile) -> List[str]:
        """Generate metric meal ideas"""
        target = nutrition_targets[0]  # Use first week targets
        
        # Calculate per-meal targets (4 meals per day)
        meal_kj = target.kJ_per_day // 4
        meal_protein = target.protein_g // 4
        meal_carbs = target.carbs_g // 4
        meal_fat = target.fat_g // 4
        
        meals = [
            f"Breakfast: 250 mL skim milk + 60 g oats + 30 g protein powder ({meal_kj} kJ)",
            f"Lunch: 150 g chicken breast + 80 g rice + 200 g vegetables + 15 mL olive oil ({meal_kj} kJ)",
            f"Dinner: 180 g salmon + 200 g sweet potato + 150 g asparagus + 1/2 avocado ({meal_kj} kJ)",
            f"Snack: 200 g Greek yogurt + 30 g almonds + 150 g berries ({meal_kj} kJ)"
        ]
        
        return meals
    
    def _generate_mobility_drills(self, pose_alerts: List[str]) -> List[str]:
        """Generate mobility drills for posture issues"""
        drills = []
        
        if "rounded_shoulders" in pose_alerts:
            drills.append("Rounded shoulders → 3 × 15 face-pulls, daily")
            drills.append("Rounded shoulders → 2 × 30 s doorway chest stretch, daily")
        
        if "anterior_pelvic_tilt" in pose_alerts:
            drills.append("Anterior pelvic tilt → 2 × 60 s hip-flexor stretch")
            drills.append("Anterior pelvic tilt → 3 × 12 glute bridges, daily")
        
        if "forward_head" in pose_alerts:
            drills.append("Forward head → 3 × 10 chin tucks, hourly")
            drills.append("Forward head → 2 × 30 s upper trap stretch")
        
        if not drills:
            drills.append("No significant posture issues detected → general mobility routine")
        
        return drills
    
    def _generate_rationale(self, profile, wizard, vision) -> List[str]:
        """Generate rationale referencing user data"""
        rationale = []
        
        # Goal-based rationale
        goal_text = profile.primaryGoal.replace("-", " ")
        rationale.append(f"Calorie target set for {goal_text} goal based on {profile.activityLvl} activity level")
        
        # Vision-based rationale
        if vision.poseAlerts:
            alerts_text = ", ".join(alert.replace("_", " ") for alert in vision.poseAlerts)
            rationale.append(f"Corrective exercises included to address {alerts_text} detected in posture analysis")
        
        # Equipment adaptations
        if wizard.equipLimits:
            limits_text = ", ".join(wizard.equipLimits)
            rationale.append(f"Exercise selection adapted for equipment limitations: {limits_text}")
        
        # Body composition insights
        bf_text = f"{vision.bfEstimate}% body fat estimate"
        if vision.bfEstimate > 25:
            rationale.append(f"Higher protein intake recommended based on {bf_text} for lean mass preservation")
        elif vision.bfEstimate < 12:
            rationale.append(f"Conservative calorie approach for lean physique ({bf_text})")
        else:
            rationale.append(f"Macro distribution optimized for {bf_text} and {goal_text} goal")
        
        # Training frequency
        rationale.append(f"{profile.trainDays}-day program matches your available training schedule")
        
        return rationale
    
    def _format_response(self, profile, nutrition_targets, training_plan, 
                        meal_ideas, mobility_drills, rationale) -> FormattedPlanResponse:
        """Format response exactly matching specification"""
        
        # Calculate estimated session duration
        main_exercises = [ex for ex in training_plan if ex.day.startswith("Day")]
        avg_exercises_per_day = len(main_exercises) / max(profile.trainDays, 1)
        estimated_duration = f"{int(avg_exercises_per_day * 8)}-{int(avg_exercises_per_day * 12)} minutes"
        
        overview = PlanOverview(
            summary=f"4-week {profile.primaryGoal.replace('-', ' ')} program for {profile.fullName} (Age {profile.age})",
            duration_weeks=4,
            training_days_per_week=profile.trainDays,
            estimated_time_per_session=estimated_duration,
            disclaimer=self.legal_disclaimer
        )
        
        return FormattedPlanResponse(
            overview=overview,
            weekly_nutrition_targets=nutrition_targets,
            training_mesocycle=training_plan,
            meal_ideas=meal_ideas,
            mobility_posture_drills=mobility_drills,
            rationale=rationale
        )

# Utility functions for plan customization
def validate_ranges(height_cm: float, weight_kg: float, bf_pct: float) -> List[ValidationError]:
    """Validate input ranges before computation"""
    errors = []
    
    if not (100 <= height_cm <= 230):
        errors.append(ValidationError(
            field="height_cm",
            message=f"Height {height_cm}cm outside valid range (100-230cm)",
            code="INVALID_RANGE"
        ))
    
    if not (30 <= weight_kg <= 300):
        errors.append(ValidationError(
            field="weight_kg", 
            message=f"Weight {weight_kg}kg outside valid range (30-300kg)",
            code="INVALID_RANGE"
        ))
    
    if not (3 <= bf_pct <= 60):
        errors.append(ValidationError(
            field="body_fat_pct",
            message=f"Body fat {bf_pct}% outside valid range (3-60%)",
            code="INVALID_RANGE"
        ))
    
    return errors

def apply_progression_rule(previous_week_rir: int, current_sets: int, current_reps: str) -> tuple:
    """
    Progression rule: if previous week's RIR ≤ 2, increase load or reps by 2.5–5%
    Returns: (new_sets, new_reps)
    """
    if previous_week_rir <= 2:
        # Increase reps by ~5%
        if "-" in current_reps:
            low, high = map(int, current_reps.split("-"))
            new_low = max(low, int(low * 1.05))
            new_high = int(high * 1.05)
            return current_sets, f"{new_low}-{new_high}"
        else:
            # Single rep number
            try:
                reps = int(current_reps)
                new_reps = int(reps * 1.05)
                return current_sets, str(new_reps)
            except ValueError:
                # Time-based (e.g., "30 s")
                return current_sets, current_reps
    
    return current_sets, current_reps

def generate_kid_safe_plan(age: int, activity_level: str) -> Dict[str, Any]:
    """
    Generate kid-safe, play-based workouts for users under 13
    No calorie counting as per specification
    """
    if age >= 13:
        raise ValueError("Kid-safe plan only for users under 13")
    
    kid_activities = [
        {"activity": "Tag Games", "duration": "10-15 minutes", "skills": "Agility, cardiovascular"},
        {"activity": "Animal Movements", "duration": "5-10 minutes", "skills": "Coordination, strength"},
        {"activity": "Obstacle Courses", "duration": "15-20 minutes", "skills": "Multi-movement, fun"},
        {"activity": "Dance/Movement", "duration": "10-15 minutes", "skills": "Rhythm, flexibility"},
        {"activity": "Ball Games", "duration": "15-20 minutes", "skills": "Hand-eye coordination"}
    ]
    
    return {
        "type": "play_based_activities",
        "age_group": f"{age} years old",
        "activities": kid_activities,
        "frequency": "Daily play time recommended",
        "nutrition": "Balanced meals with family - no calorie counting",
        "notes": "Focus on fun, movement, and healthy habits",
        "disclaimer": "Consult pediatrician for specific exercise recommendations"
    }

# Plan acceptance and tracking functions
def accept_plan(plan_id: str, user_id: str) -> Dict[str, Any]:
    """
    Handle plan acceptance - starts 28-day tracking
    Returns tracking configuration
    """
    return {
        "plan_id": plan_id,
        "user_id": user_id,
        "start_date": datetime.now().isoformat(),
        "duration_days": 28,
        "auto_progression": True,
        "next_session_prompt": True,
        "compliance_tracking": True,
        "regeneration_prompt_day": 25  # Prompt for new plan at day 25
    }

def check_compliance(user_id: str, plan_id: str, sessions_data: List[Dict]) -> Dict[str, Any]:
    """
    Check compliance and provide nudges if needed
    Per specification: ≥ 3 scheduled sessions missed within 7 days → gentle nudge
    """
    from datetime import datetime, timedelta
    
    # Get last 7 days of scheduled sessions
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_sessions = [s for s in sessions_data if s['scheduled_date'] >= seven_days_ago]
    
    missed_sessions = [s for s in recent_sessions if not s.get('completed', False)]
    
    compliance_status = {
        "user_id": user_id,
        "plan_id": plan_id,
        "last_7_days": {
            "scheduled": len(recent_sessions),
            "completed": len(recent_sessions) - len(missed_sessions),
            "missed": len(missed_sessions)
        },
        "needs_nudge": len(missed_sessions) >= 3,
        "nudge_message": None
    }
    
    if compliance_status["needs_nudge"]:
        compliance_status["nudge_message"] = (
            "We noticed you've missed a few workouts this week. "
            "Remember, consistency is key to reaching your goals. "
            "Would you like to adjust your schedule or get some motivation tips?"
        )
    
    return compliance_status

# Regeneration handling
def handle_regeneration_request(plan_id: str, user_comment: str, 
                               free_regenerations_used: int) -> Dict[str, Any]:
    """
    Handle plan regeneration requests
    Per specification: one free regeneration, then queue for email
    """
    if free_regenerations_used >= 1:
        return {
            "queued": True,
            "message": "Regeneration request queued, will email when ready",
            "estimated_time": "24-48 hours",
            "plan_id": plan_id
        }
    
    # Process immediate regeneration
    modifications = parse_user_comment(user_comment)
    
    return {
        "queued": False,
        "new_plan_id": f"regen_{plan_id}_{int(datetime.now().timestamp())}",
        "modifications_made": modifications,
        "free_regenerations_remaining": 0
    }

def parse_user_comment(comment: str) -> List[str]:
    """
    Parse user regeneration comment to identify requested changes
    E.g., "swap barbell squat for goblet squat"
    """
    modifications = []
    
    # Simple keyword detection - in production, use NLP
    if "swap" in comment.lower():
        modifications.append("Exercise substitution requested")
    
    if any(word in comment.lower() for word in ["more", "increase", "harder"]):
        modifications.append("Increased difficulty requested")
    
    if any(word in comment.lower() for word in ["less", "decrease", "easier"]):
        modifications.append("Decreased difficulty requested")
    
    if any(word in comment.lower() for word in ["time", "duration", "minutes"]):
        modifications.append("Session duration adjustment requested")
    
    if not modifications:
        modifications.append("General plan adjustment requested")
    
    return modifications

# Export main class and utilities
__all__ = [
    'GymAICoachLLM',
    'validate_ranges', 
    'apply_progression_rule',
    'generate_kid_safe_plan',
    'accept_plan',
    'check_compliance', 
    'handle_regeneration_request'
]