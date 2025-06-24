# backend/services/ - Enhanced service layer

# services/user_service.py
from typing import Optional, Dict, Any
from datetime import datetime, date
from database.models import UserProfile, UserMeasurements
from database.database import EnhancedGymDatabase

class UserService:
    def __init__(self, db: EnhancedGymDatabase):
        self.db = db
    
    def create_or_update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> str:
        """Create or update user profile"""
        profile = UserProfile(user_id=user_id, **profile_data)
        return self.db.create_or_update_profile(profile)
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self.db.get_user_profile(user_id)
    
    def is_profile_complete(self, user_id: str) -> bool:
        """Check if user profile is complete"""
        return self.db.is_profile_complete(user_id)
    
    def store_measurements(self, user_id: str, measurement_data: Dict[str, Any]) -> str:
        """Store new measurements"""
        measurements = UserMeasurements(user_id=user_id, **measurement_data)
        return self.db.store_measurements(measurements)
    
    def get_latest_measurements(self, user_id: str) -> Optional[UserMeasurements]:
        """Get latest measurements"""
        return self.db.get_latest_measurements(user_id)
    
    def can_generate_plan(self, user_id: str) -> bool:
        """Check if user can generate a plan (profile + measurements required)"""
        profile_complete = self.is_profile_complete(user_id)
        has_measurements = self.get_latest_measurements(user_id) is not None
        return profile_complete and has_measurements


# services/plan_service.py
from typing import List, Optional, Dict, Any
from database.models import CompletePlan, UserProfile, UserMeasurements, PlanStatus
from .plan_generator import Enhanced4WeekPlanGenerator
from .safety_validator import SafetyValidator

class PlanService:
    def __init__(self, db: EnhancedGymDatabase):
        self.db = db
        self.plan_generator = Enhanced4WeekPlanGenerator()
        self.safety_validator = SafetyValidator()
    
    def generate_plan(self, user_id: str, measurement_data: Dict[str, Any]) -> str:
        """Generate a new 4-week plan"""
        # Get user profile
        profile = self.db.get_user_profile(user_id)
        if not profile:
            raise ValueError("User profile not found")
        
        # Store new measurements
        measurements = UserMeasurements(user_id=user_id, **measurement_data)
        measurement_id = self.db.store_measurements(measurements)
        
        # Generate the plan
        plan = self.plan_generator.generate_complete_plan(profile, measurements)
        
        # Run safety checks
        safety_results = self.safety_validator.validate_plan(plan, profile, measurements)
        plan.safety_checks = safety_results
        
        # Store and return plan ID
        plan_id = self.db.store_plan(plan)
        return plan_id
    
    def regenerate_plan(self, original_plan_id: str, feedback: str) -> str:
        """Regenerate plan with user feedback"""
        original_plan = self.db.get_plan_by_id(original_plan_id)
        if not original_plan:
            raise ValueError("Original plan not found")
        
        # Get user profile and measurements from the original plan
        profile = original_plan.profile_snapshot
        measurements = original_plan.measurements_snapshot
        
        # Generate new plan with modifications
        new_plan = self.plan_generator.regenerate_with_feedback(
            original_plan, feedback, profile, measurements
        )
        
        # Validate safety
        safety_results = self.safety_validator.validate_plan(new_plan, profile, measurements)
        new_plan.safety_checks = safety_results
        
        return self.db.regenerate_plan(original_plan_id, new_plan, feedback)
    
    def accept_plan(self, plan_id: str) -> bool:
        """Accept and activate a plan"""
        return self.db.accept_plan(plan_id)
    
    def get_active_plan(self, user_id: str) -> Optional[CompletePlan]:
        """Get user's active plan"""
        return self.db.get_active_plan(user_id)
    
    def get_plan_history(self, user_id: str) -> List[CompletePlan]:
        """Get plan history"""
        return self.db.get_plan_history(user_id)


# services/plan_generator.py
from typing import Dict, List, Any
from database.models import (
    CompletePlan, UserProfile, UserMeasurements, WorkoutWeek, 
    WorkoutDay, Exercise, NutritionPlan, NutritionTargets, Meal
)
from utils.constants import EXERCISE_DATABASE, NUTRITION_DATABASE, SAFETY_LIMITS
from utils.helpers import calculate_bmr, calculate_tdee, parse_feedback
import uuid

class Enhanced4WeekPlanGenerator:
    def __init__(self):
        self.exercise_db = EXERCISE_DATABASE
        self.nutrition_db = NUTRITION_DATABASE
        self.safety_limits = SAFETY_LIMITS
    
    def generate_complete_plan(self, profile: UserProfile, measurements: UserMeasurements) -> CompletePlan:
        """Generate a complete 4-week plan"""
        
        # Generate 4-week workout plan
        workout_weeks = self._generate_4_week_workouts(profile, measurements)
        
        # Generate nutrition plan
        nutrition_plan = self._generate_nutrition_plan(profile, measurements)
        
        # Create complete plan
        plan = CompletePlan(
            id=str(uuid.uuid4()),
            user_id=profile.user_id,
            workout_weeks=workout_weeks,
            nutrition_plan=nutrition_plan,
            profile_snapshot=profile,
            measurements_snapshot=measurements,
            total_workouts=sum(len(week.workouts) for week in workout_weeks),
            estimated_time_per_week=sum(
                sum(workout.estimated_duration_minutes for workout in week.workouts) 
                for week in workout_weeks
            ) // 4
        )
        
        return plan
    
    def _generate_4_week_workouts(self, profile: UserProfile, measurements: UserMeasurements) -> List[WorkoutWeek]:
        """Generate 4 weeks of progressive workouts"""
        weeks = []
        
        # Determine training split based on experience and days
        split = self._get_training_split(profile.gym_experience, profile.preferred_training_days)
        
        for week_num in range(1, 5):
            # Generate base week
            workouts = self._generate_week_workouts(split, profile, week_num)
            
            # Apply progressive overload
            workouts = self._apply_progressive_overload(workouts, week_num, profile.gym_experience)
            
            week = WorkoutWeek(
                week_number=week_num,
                focus=self._get_week_focus(week_num),
                workouts=workouts,
                volume_multiplier=self._get_volume_multiplier(week_num),
                notes=self._get_week_notes(week_num)
            )
            weeks.append(week)
        
        return weeks
    
    def _get_training_split(self, experience: str, days: int) -> Dict[str, List[str]]:
        """Get appropriate training split"""
        if experience == "beginner":
            if days == 3:
                return {
                    "Day 1": ["chest", "shoulders", "triceps"],
                    "Day 2": ["back", "biceps"],
                    "Day 3": ["legs", "core"]
                }
            elif days == 4:
                return {
                    "Day 1": ["chest", "triceps"],
                    "Day 2": ["back", "biceps"],
                    "Day 3": ["legs"],
                    "Day 4": ["shoulders", "core"]
                }
        elif experience == "intermediate":
            if days == 4:
                return {
                    "Day 1": ["chest", "shoulders"],
                    "Day 2": ["back", "biceps"],
                    "Day 3": ["legs"],
                    "Day 4": ["arms", "core"]
                }
            elif days == 5:
                return {
                    "Day 1": ["chest"],
                    "Day 2": ["back"],
                    "Day 3": ["legs"],
                    "Day 4": ["shoulders"],
                    "Day 5": ["arms", "core"]
                }
        else:  # advanced
            return {
                "Day 1": ["chest", "triceps"],
                "Day 2": ["back", "biceps"],
                "Day 3": ["legs"],
                "Day 4": ["shoulders"],
                "Day 5": ["arms"],
                "Day 6": ["legs", "core"]
            }
        
        # Default fallback
        return {
            "Day 1": ["chest", "shoulders"],
            "Day 2": ["back", "biceps"],
            "Day 3": ["legs"],
            "Day 4": ["arms", "core"]
        }
    
    def _generate_week_workouts(self, split: Dict[str, List[str]], profile: UserProfile, week_num: int) -> List[WorkoutDay]:
        """Generate workouts for a week"""
        workouts = []
        
        for day_name, muscle_groups in split.items():
            exercises = self._select_exercises(muscle_groups, profile.gym_experience)
            
            # Ensure minimum 5 exercises
            while len(exercises) < 5:
                additional_exercises = self._get_additional_exercises(muscle_groups, profile.gym_experience)
                exercises.extend(additional_exercises)
                exercises = exercises[:8]  # Cap at 8 exercises max
            
            workout = WorkoutDay(
                day_number=len(workouts) + 1,
                day_name=day_name,
                muscle_groups=muscle_groups,
                exercises=exercises[:5] if len(exercises) >= 5 else exercises,  # Ensure exactly 5
                estimated_duration_minutes=self._calculate_workout_duration(exercises),
                difficulty_rating=self._calculate_difficulty_rating(exercises, profile.gym_experience)
            )
            workouts.append(workout)
        
        return workouts
    
    def _select_exercises(self, muscle_groups: List[str], experience: str) -> List[Exercise]:
        """Select appropriate exercises for muscle groups"""
        exercises = []
        
        for muscle_group in muscle_groups:
            # Get exercises for this muscle group
            available_exercises = self.exercise_db.get(muscle_group, [])
            
            # Filter by experience level
            suitable_exercises = [
                ex for ex in available_exercises 
                if self._is_suitable_for_experience(ex, experience)
            ]
            
            # Select 2 exercises per muscle group (primary focus)
            selected = suitable_exercises[:2] if suitable_exercises else []
            
            for ex_data in selected:
                exercise = Exercise(
                    name=ex_data["name"],
                    muscle_groups=[muscle_group],
                    equipment=ex_data.get("equipment", ["bodyweight"]),
                    difficulty=ex_data.get("difficulty", experience),
                    sets=self._get_sets_for_experience(experience),
                    reps=self._get_reps_for_goal_and_experience(muscle_group, experience),
                    rest_seconds=self._get_rest_time(muscle_group, experience),
                    notes=ex_data.get("notes", "Focus on proper form"),
                    substitutions=ex_data.get("substitutions", []),
                    safety_notes=ex_data.get("safety_notes")
                )
                exercises.append(exercise)
        
        return exercises
    
    def _is_suitable_for_experience(self, exercise_data: Dict, experience: str) -> bool:
        """Check if exercise is suitable for user's experience level"""
        exercise_difficulty = exercise_data.get("difficulty", "beginner")
        
        if experience == "beginner":
            return exercise_difficulty in ["beginner", "intermediate"]
        elif experience == "intermediate":
            return exercise_difficulty in ["beginner", "intermediate", "advanced"]
        else:  # advanced
            return True  # Advanced users can do all exercises
    
    def _get_sets_for_experience(self, experience: str) -> int:
        """Get appropriate number of sets based on experience"""
        sets_map = {
            "beginner": 3,
            "intermediate": 4,
            "advanced": 4
        }
        return sets_map.get(experience, 3)
    
    def _get_reps_for_goal_and_experience(self, muscle_group: str, experience: str) -> str:
        """Get rep ranges based on muscle group and experience"""
        if muscle_group in ["legs", "core"]:
            if experience == "beginner":
                return "12-15"
            else:
                return "15-20"
        else:  # Upper body
            if experience == "beginner":
                return "10-12"
            elif experience == "intermediate":
                return "8-12"
            else:
                return "6-10"
    
    def _get_rest_time(self, muscle_group: str, experience: str) -> int:
        """Get rest time based on muscle group and experience"""
        if muscle_group == "legs":
            return 90 if experience == "beginner" else 120
        elif muscle_group == "core":
            return 45
        else:
            return 60 if experience == "beginner" else 90
    
    def _get_additional_exercises(self, muscle_groups: List[str], experience: str) -> List[Exercise]:
        """Get additional exercises to reach minimum 5"""
        additional = []
        
        # Add core exercises if not primary focus
        if "core" not in muscle_groups:
            core_exercises = self.exercise_db.get("core", [])[:2]
            for ex_data in core_exercises:
                exercise = Exercise(
                    name=ex_data["name"],
                    muscle_groups=["core"],
                    equipment=ex_data.get("equipment", ["bodyweight"]),
                    difficulty="beginner",
                    sets=2,
                    reps="15-20",
                    rest_seconds=45,
                    notes="Accessory movement for core stability"
                )
                additional.append(exercise)
        
        return additional
    
    def _apply_progressive_overload(self, workouts: List[WorkoutDay], week_num: int, experience: str) -> List[WorkoutDay]:
        """Apply progressive overload based on week number"""
        multipliers = {
            1: 1.0,    # Base week
            2: 1.05,   # 5% increase
            3: 1.10,   # 10% increase
            4: 0.8 if experience != "beginner" else 1.0  # Deload for experienced, maintain for beginners
        }
        
        multiplier = multipliers[week_num]
        
        for workout in workouts:
            for exercise in workout.exercises:
                if week_num == 4 and experience != "beginner":
                    # Deload week - reduce volume
                    exercise.sets = max(2, int(exercise.sets * 0.8))
                    exercise.notes += f" | Week 4 Deload: Reduced volume for recovery"
                else:
                    # Progressive overload
                    if week_num > 1:
                        # Increase reps slightly
                        if "-" in exercise.reps:
                            low, high = map(int, exercise.reps.split("-"))
                            new_high = min(20, int(high * multiplier))
                            exercise.reps = f"{low}-{new_high}"
                        
                        exercise.weight_progression = f"Week {week_num}: +2.5-5% weight from previous week"
                        exercise.notes += f" | Week {week_num}: Progressive overload applied"
        
        return workouts
    
    def _calculate_workout_duration(self, exercises: List[Exercise]) -> int:
        """Calculate estimated workout duration"""
        total_time = 0
        
        for exercise in exercises:
            # Time per set (work + rest)
            work_time = 30  # seconds per set
            set_time = work_time + exercise.rest_seconds
            total_time += exercise.sets * set_time
        
        # Add warm-up and cool-down
        total_time += 10 * 60  # 10 minutes
        
        return int(total_time / 60)  # Convert to minutes
    
    def _calculate_difficulty_rating(self, exercises: List[Exercise], experience: str) -> int:
        """Calculate overall workout difficulty"""
        base_difficulty = {
            "beginner": 4,
            "intermediate": 6,
            "advanced": 8
        }
        
        # Adjust based on exercise count and complexity
        difficulty = base_difficulty.get(experience, 5)
        
        if len(exercises) > 6:
            difficulty += 1
        
        return min(10, difficulty)
    
    def _get_week_focus(self, week_num: int) -> str:
        """Get focus description for each week"""
        focuses = {
            1: "Foundation - Learning movements and building base",
            2: "Development - Increasing intensity and volume",
            3: "Peak - Maximum effort and progressive overload",
            4: "Recovery - Active recovery and preparation for next cycle"
        }
        return focuses[week_num]
    
    def _get_volume_multiplier(self, week_num: int) -> float:
        """Get volume multiplier for each week"""
        multipliers = {1: 1.0, 2: 1.05, 3: 1.10, 4: 0.8}
        return multipliers[week_num]
    
    def _get_week_notes(self, week_num: int) -> str:
        """Get specific notes for each week"""
        notes = {
            1: "Focus on proper form and technique. Don't rush through movements.",
            2: "Increase weight slightly if exercises feel too easy. Listen to your body.",
            3: "Push yourself harder this week. This is your peak intensity week.",
            4: "Recovery week - lighter weights, focus on mobility and active recovery."
        }
        return notes[week_num]
    
    def _generate_nutrition_plan(self, profile: UserProfile, measurements: UserMeasurements) -> NutritionPlan:
        """Generate comprehensive nutrition plan"""
        # Calculate BMR and TDEE
        bmr = calculate_bmr(measurements.weight_kg, measurements.height_cm, profile.age, profile.sex.value)
        tdee = calculate_tdee(bmr, profile.activity_level.value)
        
        # Adjust calories based on goal
        calorie_adjustment = self._get_calorie_adjustment(profile.primary_fitness_goal)
        target_calories = int(tdee * calorie_adjustment)
        
        # Apply safety limits
        min_calories = self.safety_limits["min_calories"][profile.sex.value]
        target_calories = max(target_calories, min_calories)
        
        # Calculate macros
        macros = self._calculate_macros(target_calories, profile.primary_fitness_goal, measurements.weight_kg)
        
        # Create nutrition targets
        targets = NutritionTargets(
            calories=target_calories,
            protein_g=macros["protein"],
            carbs_g=macros["carbs"],
            fat_g=macros["fat"],
            fiber_g=max(25, int(target_calories / 80)),  # ~25-35g fiber
            water_ml=int(measurements.weight_kg * 35)  # 35ml per kg
        )
        
        # Generate meal plan
        meal_plan = self._generate_meal_plan(targets, profile)
        
        # Create nutrition plan
        nutrition_plan = NutritionPlan(
            daily_targets=targets,
            bmr=int(bmr),
            tdee=int(tdee),
            calorie_adjustment=calorie_adjustment - 1.0,  # Show as percentage
            meal_plan=meal_plan,
            hydration_schedule=self._create_hydration_schedule(),
            nutrition_tips=self._get_nutrition_tips(profile.primary_fitness_goal),
            meal_timing_advice=self._get_meal_timing_advice(),
            dos_and_donts=self._get_nutrition_dos_and_donts()
        )
        
        return nutrition_plan
    
    def _get_calorie_adjustment(self, goal: str) -> float:
        """Get calorie adjustment multiplier based on goal"""
        adjustments = {
            "lose_fat": 0.85,      # 15% deficit
            "gain_muscle": 1.15,   # 15% surplus
            "strength": 1.10,      # 10% surplus
            "recomposition": 1.0,  # Maintenance
            "maintenance": 1.0     # Maintenance
        }
        return adjustments.get(goal, 1.0)
    
    def _calculate_macros(self, calories: int, goal: str, weight_kg: float) -> Dict[str, int]:
        """Calculate macro distribution"""
        if goal == "lose_fat":
            protein_ratio = 0.35
            fat_ratio = 0.25
            carb_ratio = 0.40
        elif goal in ["gain_muscle", "strength"]:
            protein_ratio = 0.30
            fat_ratio = 0.25
            carb_ratio = 0.45
        elif goal == "recomposition":
            protein_ratio = 0.35
            fat_ratio = 0.30
            carb_ratio = 0.35
        else:  # maintenance
            protein_ratio = 0.25
            fat_ratio = 0.30
            carb_ratio = 0.45
        
        # Ensure minimum protein (1.6-2.2g per kg body weight)
        min_protein = max(weight_kg * 1.6, calories * protein_ratio / 4)
        
        protein_g = int(min_protein)
        fat_g = int(calories * fat_ratio / 9)
        
        # Remaining calories go to carbs
        remaining_calories = calories - (protein_g * 4) - (fat_g * 9)
        carb_g = int(remaining_calories / 4)
        
        return {
            "protein": protein_g,
            "carbs": carb_g,
            "fat": fat_g
        }
    
    def _generate_meal_plan(self, targets: NutritionTargets, profile: UserProfile) -> List[Meal]:
        """Generate daily meal plan"""
        meals = []
        
        # Meal distribution
        meal_distribution = {
            "breakfast": 0.25,
            "lunch": 0.35,
            "dinner": 0.30,
            "snack": 0.10
        }
        
        for meal_type, ratio in meal_distribution.items():
            meal_calories = int(targets.calories * ratio)
            meal_protein = int(targets.protein_g * ratio)
            meal_carbs = int(targets.carbs_g * ratio)
            meal_fat = int(targets.fat_g * ratio)
            
            # Get meal template
            meal_template = self._get_meal_template(meal_type, profile)
            
            meal = Meal(
                meal_type=meal_type,
                name=meal_template["name"],
                description=meal_template.get("description", ""),
                calories=meal_calories,
                protein_g=meal_protein,
                carbs_g=meal_carbs,
                fat_g=meal_fat,
                prep_time_minutes=meal_template.get("prep_time", 15),
                ingredients=meal_template["ingredients"],
                instructions=meal_template.get("instructions", []),
                dietary_tags=meal_template.get("tags", [])
            )
            meals.append(meal)
        
        return meals
    
    def _get_meal_template(self, meal_type: str, profile: UserProfile) -> Dict[str, Any]:
        """Get meal template based on type and preferences"""
        templates = self.nutrition_db.get(meal_type, [])
        
        # Filter by dietary restrictions
        suitable_templates = [
            t for t in templates 
            if not any(restriction in t.get("tags", []) for restriction in profile.dietary_restrictions)
        ]
        
        # Return first suitable template or fallback
        return suitable_templates[0] if suitable_templates else {
            "name": f"Custom {meal_type.title()}",
            "ingredients": ["Protein source", "Carbohydrate source", "Healthy fats", "Vegetables"],
            "prep_time": 15,
            "tags": []
        }
    
    def _create_hydration_schedule(self) -> List[str]:
        """Create hydration reminders throughout the day"""
        return [
            "Wake up: 1 glass of water",
            "Before breakfast: 1 glass",
            "Mid-morning: 1 glass",
            "Before lunch: 1 glass",
            "Afternoon: 1 glass",
            "Pre-workout: 1 glass",
            "Post-workout: 2 glasses",
            "Before dinner: 1 glass",
            "Evening: 1 glass"
        ]
    
    def _get_nutrition_tips(self, goal: str) -> List[str]:
        """Get goal-specific nutrition tips"""
        base_tips = [
            "Eat protein with every meal to support muscle growth and recovery",
            "Include a variety of colorful vegetables for micronutrients",
            "Time your carbohydrates around your workouts for optimal energy",
            "Stay consistent with your meal timing to regulate hunger"
        ]
        
        goal_specific = {
            "lose_fat": [
                "Focus on high-volume, low-calorie foods to stay satisfied",
                "Consider intermittent fasting if it fits your lifestyle",
                "Prioritize protein to preserve muscle mass during fat loss"
            ],
            "gain_muscle": [
                "Don't skip meals - consistent eating supports muscle growth",
                "Include post-workout nutrition within 2 hours of training",
                "Consider a casein protein shake before bed"
            ],
            "strength": [
                "Fuel your workouts with adequate carbohydrates",
                "Focus on nutrient timing around training sessions",
                "Include creatine supplementation if desired"
            ]
        }
        
        return base_tips + goal_specific.get(goal, [])
    
    def _get_meal_timing_advice(self) -> List[str]:
        """Get meal timing advice"""
        return [
            "Eat breakfast within 1-2 hours of waking up",
            "Have a balanced meal 2-3 hours before workouts",
            "Include protein and carbs within 2 hours post-workout",
            "Stop eating 2-3 hours before bedtime",
            "Space meals 3-4 hours apart for optimal digestion"
        ]
    
    def _get_nutrition_dos_and_donts(self) -> Dict[str, List[str]]:
        """Get nutrition dos and don'ts"""
        return {
            "dos": [
                "Plan and prep meals in advance",
                "Read nutrition labels and track portions",
                "Stay hydrated throughout the day",
                "Include a variety of whole foods",
                "Listen to your hunger and fullness cues",
                "Allow for occasional treats in moderation"
            ],
            "donts": [
                "Skip meals or go long periods without eating",
                "Rely heavily on processed foods",
                "Drink your calories (except post-workout shakes)",
                "Follow extreme or unsustainable diets",
                "Ignore portion sizes",
                "Eliminate entire food groups without medical reason"
            ]
        }
    
    def regenerate_with_feedback(self, original_plan: CompletePlan, feedback: str, 
                               profile: UserProfile, measurements: UserMeasurements) -> CompletePlan:
        """Regenerate plan with user feedback"""
        # Parse feedback for specific requests
        modifications = parse_feedback(feedback)
        
        # Start with original plan
        new_plan = original_plan.copy(deep=True)
        new_plan.id = str(uuid.uuid4())
        new_plan.status = "draft"
        new_plan.user_feedback = feedback
        
        # Apply modifications
        if "replace_exercises" in modifications:
            new_plan.workout_weeks = self._apply_exercise_substitutions(
                new_plan.workout_weeks, modifications["replace_exercises"]
            )
        
        if "reduce_time" in modifications:
            new_plan.workout_weeks = self._reduce_workout_time(
                new_plan.workout_weeks, modifications["reduce_time"]
            )
        
        if "change_nutrition" in modifications:
            new_plan.nutrition_plan = self._modify_nutrition_plan(
                new_plan.nutrition_plan, modifications["change_nutrition"]
            )
        
        return new_plan
    
    def _apply_exercise_substitutions(self, workout_weeks: List[WorkoutWeek], 
                                   substitutions: Dict[str, str]) -> List[WorkoutWeek]:
        """Apply exercise substitutions based on feedback"""
        for week in workout_weeks:
            for workout in week.workouts:
                for i, exercise in enumerate(workout.exercises):
                    for original, replacement in substitutions.items():
                        if original.lower() in exercise.name.lower():
                            # Find replacement exercise
                            replacement_exercise = self._find_replacement_exercise(
                                exercise, replacement, workout.muscle_groups
                            )
                            if replacement_exercise:
                                workout.exercises[i] = replacement_exercise
        
        return workout_weeks
    
    def _find_replacement_exercise(self, original: Exercise, replacement_name: str, 
                                 muscle_groups: List[str]) -> Optional[Exercise]:
        """Find a suitable replacement exercise"""
        # Search through exercise database for replacement
        for muscle_group in muscle_groups:
            exercises = self.exercise_db.get(muscle_group, [])
            for ex_data in exercises:
                if replacement_name.lower() in ex_data["name"].lower():
                    return Exercise(
                        name=ex_data["name"],
                        muscle_groups=[muscle_group],
                        equipment=ex_data.get("equipment", ["bodyweight"]),
                        difficulty=ex_data.get("difficulty", "intermediate"),
                        sets=original.sets,
                        reps=original.reps,
                        rest_seconds=original.rest_seconds,
                        notes=f"Substituted for {original.name}",
                        substitutions=ex_data.get("substitutions", [])
                    )
        
        return None


# services/safety_validator.py
from typing import Dict, Any
from database.models import CompletePlan, UserProfile, UserMeasurements
from utils.constants import SAFETY_LIMITS

class SafetyValidator:
    def __init__(self):
        self.limits = SAFETY_LIMITS
    
    def validate_plan(self, plan: CompletePlan, profile: UserProfile, 
                     measurements: UserMeasurements) -> Dict[str, bool]:
        """Validate plan for safety compliance"""
        results = {}
        
        # Nutrition safety checks
        results["minimum_calories_met"] = self._check_minimum_calories(
            plan.nutrition_plan.daily_targets.calories, profile.sex.value
        )
        
        results["deficit_within_limits"] = self._check_deficit_limits(
            plan.nutrition_plan.calorie_adjustment
        )
        
        results["protein_adequate"] = self._check_protein_adequacy(
            plan.nutrition_plan.daily_targets.protein_g, measurements.weight_kg
        )
        
        # Workout safety checks
        results["training_frequency_safe"] = self._check_training_frequency(
            len(plan.workout_weeks[0].workouts), profile.gym_experience.value
        )
        
        results["exercise_progression_safe"] = self._check_exercise_progression(
            plan.workout_weeks, profile.gym_experience.value
        )
        
        return results
    
    def _check_minimum_calories(self, calories: int, sex: str) -> bool:
        """Check if calories meet minimum requirements"""
        min_calories = self.limits["min_calories"][sex]
        return calories >= min_calories
    
    def _check_deficit_limits(self, deficit_percentage: float) -> bool:
        """Check if calorie deficit is within safe limits"""
        return abs(deficit_percentage) <= self.limits["max_deficit"]
    
    def _check_protein_adequacy(self, protein_g: int, weight_kg: float) -> bool:
        """Check if protein meets minimum requirements"""
        min_protein = weight_kg * self.limits["min_protein_per_kg"]
        return protein_g >= min_protein
    
    def _check_training_frequency(self, workouts_per_week: int, experience: str) -> bool:
        """Check if training frequency is appropriate"""
        max_days = self.limits["max_training_days"][experience]
        return workouts_per_week <= max_days
    
    def _check_exercise_progression(self, workout_weeks: List[WorkoutWeek], 
                                  experience: str) -> bool:
        """Check if exercise progression is safe"""
        progression_limit = self.limits["progression_limits"][experience]["volume_increase"]
        
        # Check if volume increase between weeks is within limits
        for i in range(1, len(workout_weeks)):
            current_multiplier = workout_weeks[i].volume_multiplier
            previous_multiplier = workout_weeks[i-1].volume_multiplier
            
            if current_multiplier > previous_multiplier:
                increase = (current_multiplier - previous_multiplier) / previous_multiplier
                if increase > progression_limit:
                    return False
        
        return True