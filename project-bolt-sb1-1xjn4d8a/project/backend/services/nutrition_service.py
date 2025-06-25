from typing import Dict, List, Any, Optional
from database.models import NutritionPlan, NutritionTargets, Meal
import math

class NutritionService:
    def __init__(self):
        self.meal_database = self._load_meal_database()
        
    def calculate_nutrition_targets(self, user_data: Dict[str, Any], goal: str) -> NutritionTargets:
        """Calculate personalized nutrition targets"""
        # Calculate BMR
        bmr = self._calculate_bmr(
            weight_kg=user_data['weight_kg'],
            height_cm=user_data['height_cm'],
            age=user_data['age'],
            sex=user_data['sex']
        )
        
        # Calculate TDEE
        tdee = self._calculate_tdee(bmr, user_data.get('activity_level', 'moderate'))
        
        # Adjust for goal
        target_calories = self._adjust_calories_for_goal(tdee, goal)
        
        # Calculate macros
        macros = self._calculate_macros(target_calories, goal, user_data['weight_kg'])
        
        # Calculate other nutrients
        fiber_g = max(25, int(target_calories / 80))
        water_ml = int(user_data['weight_kg'] * 35)
        
        return NutritionTargets(
            calories=target_calories,
            protein_g=macros['protein'],
            carbs_g=macros['carbs'],
            fat_g=macros['fat'],
            fiber_g=fiber_g,
            water_ml=water_ml,
            sodium_mg=2300,
            calcium_mg=1000,
            iron_mg=18 if user_data['sex'] == 'female' else 8
        )
    
    def generate_meal_plan(self, targets: NutritionTargets, preferences: Dict[str, Any]) -> List[Meal]:
        """Generate a daily meal plan"""
        meal_distribution = {
            'breakfast': 0.25,
            'lunch': 0.35,
            'dinner': 0.30,
            'snack': 0.10
        }
        
        meals = []
        for meal_type, ratio in meal_distribution.items():
            meal_calories = int(targets.calories * ratio)
            meal_protein = int(targets.protein_g * ratio)
            meal_carbs = int(targets.carbs_g * ratio)
            meal_fat = int(targets.fat_g * ratio)
            
            # Find suitable meal from database
            suitable_meal = self._find_suitable_meal(
                meal_type=meal_type,
                target_calories=meal_calories,
                dietary_restrictions=preferences.get('dietary_restrictions', [])
            )
            
            # Adjust portions
            adjusted_meal = self._adjust_meal_portions(
                suitable_meal,
                meal_calories,
                meal_protein,
                meal_carbs,
                meal_fat
            )
            
            meals.append(adjusted_meal)
        
        return meals
    
    def _calculate_bmr(self, weight_kg: float, height_cm: float, age: int, sex: str) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
        if sex.lower() == 'male':
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        return bmr
    
    def _calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Calculate Total Daily Energy Expenditure"""
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'athlete': 1.9
        }
        return bmr * activity_multipliers.get(activity_level, 1.55)
    
    def _adjust_calories_for_goal(self, tdee: float, goal: str) -> int:
        """Adjust calories based on fitness goal"""
        adjustments = {
            'lose_fat': 0.85,      # 15% deficit
            'gain_muscle': 1.15,   # 15% surplus
            'strength': 1.10,      # 10% surplus
            'recomposition': 1.0,  # Maintenance
            'maintenance': 1.0     # Maintenance
        }
        
        adjusted = tdee * adjustments.get(goal, 1.0)
        
        # Apply safety limits
        if goal == 'lose_fat':
            # Ensure minimum calories
            min_calories = 1500 if self.user_sex == 'male' else 1200
            adjusted = max(adjusted, min_calories)
        
        return int(adjusted)
    
    def _calculate_macros(self, calories: int, goal: str, weight_kg: float) -> Dict[str, int]:
        """Calculate macronutrient distribution"""
        # Goal-specific macro ratios
        macro_ratios = {
            'lose_fat': {'protein': 0.35, 'fat': 0.25, 'carbs': 0.40},
            'gain_muscle': {'protein': 0.30, 'fat': 0.25, 'carbs': 0.45},
            'strength': {'protein': 0.30, 'fat': 0.30, 'carbs': 0.40},
            'recomposition': {'protein': 0.35, 'fat': 0.30, 'carbs': 0.35},
            'maintenance': {'protein': 0.25, 'fat': 0.30, 'carbs': 0.45}
        }
        
        ratios = macro_ratios.get(goal, macro_ratios['maintenance'])
        
        # Calculate grams
        protein_calories = calories * ratios['protein']
        fat_calories = calories * ratios['fat']
        carb_calories = calories * ratios['carbs']
        
        # Ensure minimum protein (1.6g per kg for muscle building goals)
        min_protein = weight_kg * (1.6 if goal in ['gain_muscle', 'strength'] else 1.2)
        
        protein_g = max(int(protein_calories / 4), int(min_protein))
        fat_g = int(fat_calories / 9)
        
        # Remaining calories go to carbs
        remaining_calories = calories - (protein_g * 4) - (fat_g * 9)
        carb_g = int(remaining_calories / 4)
        
        return {
            'protein': protein_g,
            'carbs': carb_g,
            'fat': fat_g
        }
    
    def _load_meal_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load meal database (in production, this would come from a real database)"""
        return {
            'breakfast': [
                {
                    'name': 'Protein Oatmeal Bowl',
                    'base_calories': 400,
                    'base_protein': 25,
                    'base_carbs': 55,
                    'base_fat': 10,
                    'ingredients': ['Oats', 'Protein powder', 'Berries', 'Almond butter'],
                    'prep_time': 10,
                    'tags': ['vegetarian', 'high_protein']
                },
                {
                    'name': 'Egg White Veggie Scramble',
                    'base_calories': 350,
                    'base_protein': 30,
                    'base_carbs': 20,
                    'base_fat': 15,
                    'ingredients': ['Egg whites', 'Spinach', 'Mushrooms', 'Feta cheese'],
                    'prep_time': 15,
                    'tags': ['vegetarian', 'low_carb', 'high_protein']
                }
            ],
            'lunch': [
                {
                    'name': 'Grilled Chicken Power Bowl',
                    'base_calories': 500,
                    'base_protein': 40,
                    'base_carbs': 45,
                    'base_fat': 15,
                    'ingredients': ['Chicken breast', 'Quinoa', 'Mixed vegetables', 'Avocado'],
                    'prep_time': 25,
                    'tags': ['high_protein', 'balanced']
                },
                {
                    'name': 'Salmon and Sweet Potato',
                    'base_calories': 550,
                    'base_protein': 35,
                    'base_carbs': 50,
                    'base_fat': 20,
                    'ingredients': ['Salmon', 'Sweet potato', 'Broccoli', 'Olive oil'],
                    'prep_time': 30,
                    'tags': ['omega3', 'anti_inflammatory']
                }
            ],
            'dinner': [
                {
                    'name': 'Lean Beef Stir-fry',
                    'base_calories': 480,
                    'base_protein': 35,
                    'base_carbs': 40,
                    'base_fat': 18,
                    'ingredients': ['Lean beef', 'Brown rice', 'Mixed vegetables', 'Soy sauce'],
                    'prep_time': 25,
                    'tags': ['high_protein', 'high_iron']
                },
                {
                    'name': 'Turkey Meatballs with Pasta',
                    'base_calories': 520,
                    'base_protein': 32,
                    'base_carbs': 65,
                    'base_fat': 12,
                    'ingredients': ['Ground turkey', 'Whole wheat pasta', 'Marinara sauce', 'Basil'],
                    'prep_time': 35,
                    'tags': ['lean_protein', 'comfort_food']
                }
            ],
            'snack': [
                {
                    'name': 'Greek Yogurt Parfait',
                    'base_calories': 200,
                    'base_protein': 20,
                    'base_carbs': 25,
                    'base_fat': 3,
                    'ingredients': ['Greek yogurt', 'Granola', 'Berries', 'Honey'],
                    'prep_time': 5,
                    'tags': ['vegetarian', 'high_protein', 'quick']
                },
                {
                    'name': 'Protein Smoothie',
                    'base_calories': 250,
                    'base_protein': 25,
                    'base_carbs': 30,
                    'base_fat': 5,
                    'ingredients': ['Protein powder', 'Banana', 'Spinach', 'Almond milk'],
                    'prep_time': 5,
                    'tags': ['vegetarian', 'post_workout', 'quick']
                }
            ]
        }
    
    def _find_suitable_meal(self, meal_type: str, target_calories: int, 
                          dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Find a suitable meal from the database"""
        meals = self.meal_database.get(meal_type, [])
        
        # Filter by dietary restrictions
        suitable_meals = []
        for meal in meals:
            if not any(restriction in meal.get('tags', []) for restriction in dietary_restrictions):
                suitable_meals.append(meal)
        
        if not suitable_meals:
            suitable_meals = meals  # Fallback if no meals match restrictions
        
        # Find meal closest to target calories
        best_meal = min(suitable_meals, 
                       key=lambda m: abs(m['base_calories'] - target_calories))
        
        return best_meal
    
    def _adjust_meal_portions(self, meal: Dict[str, Any], target_calories: int,
                            target_protein: int, target_carbs: int, target_fat: int) -> Meal:
        """Adjust meal portions to meet targets"""
        # Calculate scaling factor based on calories
        scale_factor = target_calories / meal['base_calories']
        
        # Apply scaling to macros
        adjusted_protein = int(meal['base_protein'] * scale_factor)
        adjusted_carbs = int(meal['base_carbs'] * scale_factor)
        adjusted_fat = int(meal['base_fat'] * scale_factor)
        
        # Fine-tune to match targets more closely
        protein_diff = target_protein - adjusted_protein
        carb_diff = target_carbs - adjusted_carbs
        fat_diff = target_fat - adjusted_fat
        
        # Adjust within reasonable bounds (±20%)
        final_protein = adjusted_protein + min(max(protein_diff, -5), 5)
        final_carbs = adjusted_carbs + min(max(carb_diff, -10), 10)
        final_fat = adjusted_fat + min(max(fat_diff, -3), 3)
        
        # Recalculate calories
        final_calories = (final_protein * 4) + (final_carbs * 4) + (final_fat * 9)
        
        return Meal(
            meal_type=meal_type,
            name=meal['name'],
            description=f"Portion adjusted for your targets",
            calories=final_calories,
            protein_g=final_protein,
            carbs_g=final_carbs,
            fat_g=final_fat,
            fiber_g=int(final_carbs * 0.1),  # Rough estimate
            prep_time_minutes=meal['prep_time'],
            ingredients=meal['ingredients'],
            instructions=[],
            dietary_tags=meal.get('tags', [])
        )

    def validate_nutrition_plan(self, plan: NutritionPlan, user_data: Dict[str, Any]) -> Dict[str, bool]:
        """Validate nutrition plan for safety and effectiveness"""
        validations = {}
        
        # Check minimum calories
        min_calories = 1500 if user_data['sex'] == 'male' else 1200
        validations['minimum_calories_met'] = plan.daily_targets.calories >= min_calories
        
        # Check protein adequacy (minimum 0.8g per kg body weight)
        min_protein = user_data['weight_kg'] * 0.8
        validations['adequate_protein'] = plan.daily_targets.protein_g >= min_protein
        
        # Check if deficit is within safe limits (max 25%)
        if hasattr(plan, 'tdee') and plan.tdee > 0:
            deficit_percentage = (plan.tdee - plan.daily_targets.calories) / plan.tdee
            validations['safe_deficit'] = deficit_percentage <= 0.25
        else:
            validations['safe_deficit'] = True
        
        # Check macro balance
        total_macro_calories = (
            (plan.daily_targets.protein_g * 4) +
            (plan.daily_targets.carbs_g * 4) +
            (plan.daily_targets.fat_g * 9)
        )
        macro_deviation = abs(total_macro_calories - plan.daily_targets.calories)
        validations['macros_balanced'] = macro_deviation < 50  # Within 50 calories
        
        # Check fiber adequacy
        validations['adequate_fiber'] = plan.daily_targets.fiber_g >= 25
        
        # Check hydration
        min_water = user_data['weight_kg'] * 30  # 30ml per kg minimum
        validations['adequate_hydration'] = plan.daily_targets.water_ml >= min_water
        
        return validations
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> List[str]:
        """Validate password strength and return list of issues"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        return issues
    
    @staticmethod
    def validate_measurements(measurements: Dict[str, Any]) -> List[str]:
        """Validate body measurements"""
        errors = []
        
        # Height validation
        height = measurements.get("height_cm")
        if height is not None:
            if not isinstance(height, (int, float)):
                errors.append("Height must be a number")
            elif height < 100 or height > 250:
                errors.append("Height must be between 100-250 cm")
        
        # Weight validation
        weight = measurements.get("weight_kg")
        if weight is not None:
            if not isinstance(weight, (int, float)):
                errors.append("Weight must be a number")
            elif weight < 30 or weight > 300:
                errors.append("Weight must be between 30-300 kg")
        
        # Body fat validation
        body_fat = measurements.get("body_fat_percentage")
        if body_fat is not None:
            if not isinstance(body_fat, (int, float)):
                errors.append("Body fat percentage must be a number")
            elif body_fat < 3 or body_fat > 50:
                errors.append("Body fat percentage must be between 3-50%")
        
        # Muscle mass validation
        muscle_mass = measurements.get("muscle_mass_percentage")
        if muscle_mass is not None:
            if not isinstance(muscle_mass, (int, float)):
                errors.append("Muscle mass percentage must be a number")
            elif muscle_mass < 20 or muscle_mass > 60:
                errors.append("Muscle mass percentage must be between 20-60%")
        
        # Visceral fat validation
        visceral_fat = measurements.get("visceral_fat")
        if visceral_fat is not None:
            if not isinstance(visceral_fat, (int, float)):
                errors.append("Visceral fat must be a number")
            elif visceral_fat < 1 or visceral_fat > 30:
                errors.append("Visceral fat must be between 1-30")
        
        return errors
    
    @staticmethod
    def validate_profile_data(profile_data: Dict[str, Any]) -> List[str]:
        """Validate user profile data"""
        errors = []
        
        # Required fields
        required_fields = ["full_name", "date_of_birth", "sex", "primary_fitness_goal"]
        for field in required_fields:
            if not profile_data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        # Full name validation
        full_name = profile_data.get("full_name", "")
        if full_name and (len(full_name) < 2 or len(full_name) > 100):
            errors.append("Full name must be between 2-100 characters")
        
        # Date of birth validation
        dob = profile_data.get("date_of_birth")
        if dob:
            try:
                if isinstance(dob, str):
                    dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                else:
                    dob_date = dob
                
                age = Validators._calculate_age(dob_date)
                if age < 13:
                    errors.append("Must be at least 13 years old")
                elif age > 100:
                    errors.append("Age must be less than 100 years")
            except (ValueError, TypeError):
                errors.append("Invalid date of birth format (use YYYY-MM-DD)")
        
        # Sex validation
        sex = profile_data.get("sex")
        if sex and sex not in ["male", "female"]:
            errors.append("Sex must be 'male' or 'female'")
        
        # Fitness goal validation
        valid_goals = ["lose_fat", "gain_muscle", "strength", "recomposition", "maintenance"]
        goal = profile_data.get("primary_fitness_goal")
        if goal and goal not in valid_goals:
            errors.append(f"Invalid fitness goal. Must be one of: {', '.join(valid_goals)}")
        
        # Training days validation
        training_days = profile_data.get("preferred_training_days")
        if training_days is not None:
            if not isinstance(training_days, int):
                errors.append("Training days must be a number")
            elif training_days < 3 or training_days > 6:
                errors.append("Training days must be between 3-6 days per week")
        
        # Activity level validation
        valid_activity_levels = ["sedentary", "light", "moderate", "active", "athlete"]
        activity_level = profile_data.get("activity_level")
        if activity_level and activity_level not in valid_activity_levels:
            errors.append(f"Invalid activity level. Must be one of: {', '.join(valid_activity_levels)}")
        
        # Experience level validation
        valid_experience = ["beginner", "intermediate", "advanced"]
        experience = profile_data.get("gym_experience")
        if experience and experience not in valid_experience:
            errors.append(f"Invalid experience level. Must be one of: {', '.join(valid_experience)}")
        
        return errors
    
    @staticmethod
    def validate_workout_plan(plan: Dict[str, Any]) -> List[str]:
        """Validate workout plan structure"""
        errors = []
        
        if "workout_weeks" not in plan:
            errors.append("Workout plan must contain workout weeks")
            return errors
        
        weeks = plan.get("workout_weeks", [])
        if len(weeks) != 4:
            errors.append("Workout plan must contain exactly 4 weeks")
        
        for i, week in enumerate(weeks):
            if "week_number" not in week:
                errors.append(f"Week {i+1} missing week number")
            
            if "workouts" not in week:
                errors.append(f"Week {i+1} missing workouts")
                continue
            
            for j, workout in enumerate(week.get("workouts", [])):
                if "exercises" not in workout:
                    errors.append(f"Week {i+1}, Workout {j+1} missing exercises")
                elif len(workout["exercises"]) < 5:
                    errors.append(f"Week {i+1}, Workout {j+1} must have at least 5 exercises")
        
        return errors
    
    @staticmethod
    def validate_nutrition_plan(plan: Dict[str, Any]) -> List[str]:
        """Validate nutrition plan structure"""
        errors = []
        
        if "daily_targets" not in plan:
            errors.append("Nutrition plan must contain daily targets")
            return errors
        
        targets = plan.get("daily_targets", {})
        required_nutrients = ["calories", "protein_g", "carbs_g", "fat_g"]
        
        for nutrient in required_nutrients:
            if nutrient not in targets:
                errors.append(f"Daily targets missing {nutrient}")
            elif targets[nutrient] <= 0:
                errors.append(f"{nutrient} must be greater than 0")
        
        # Check calorie minimums
        calories = targets.get("calories", 0)
        if calories < 1200:
            errors.append("Calories must be at least 1200 for safety")
        
        # Check protein minimum
        protein = targets.get("protein_g", 0)
        if protein < 50:
            errors.append("Protein must be at least 50g daily")
        
        return errors
    
    @staticmethod
    def validate_image_file(file_content_type: str, file_size: int) -> List[str]:
        """Validate uploaded image file"""
        errors = []
        
        # Check file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if file_content_type not in allowed_types:
            errors.append("File must be JPEG or PNG image")
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            errors.append("File size must be less than 10MB")
        
        return errors
    
    @staticmethod
    def _calculate_age(date_of_birth: date) -> int:
        """Calculate age from date of birth"""
        today = date.today()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        # Remove any HTML tags
        cleaned = re.sub(r'<[^>]+>', '', input_string)
        # Remove any script tags specifically
        cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        # Limit length
        cleaned = cleaned[:1000]
        return cleaned.strip()