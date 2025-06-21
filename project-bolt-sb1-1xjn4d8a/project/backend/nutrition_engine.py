from typing import Dict, List, Any, Optional
import json

def calculate_bmr_harris_benedict(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Calculate Basal Metabolic Rate using Harris-Benedict equation"""
    if sex.lower() == "male":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return bmr

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure"""
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    return bmr * activity_multipliers.get(activity_level, 1.55)

def calculate_macros(calories: int, goal: str) -> Dict[str, int]:
    """Calculate macronutrient targets based on calories and goal"""
    if goal == "lose_fat":
        # Higher protein, moderate carbs, lower fat
        protein_ratio = 0.35
        carb_ratio = 0.35
        fat_ratio = 0.30
    elif goal == "gain_muscle":
        # High protein, higher carbs, moderate fat
        protein_ratio = 0.30
        carb_ratio = 0.45
        fat_ratio = 0.25
    elif goal == "recomposition":
        # High protein, moderate carbs and fat
        protein_ratio = 0.35
        carb_ratio = 0.35
        fat_ratio = 0.30
    else:  # maintenance
        protein_ratio = 0.25
        carb_ratio = 0.45
        fat_ratio = 0.30
    
    protein_calories = calories * protein_ratio
    carb_calories = calories * carb_ratio
    fat_calories = calories * fat_ratio
    
    # Convert to grams (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
    protein_g = int(protein_calories / 4)
    carbs_g = int(carb_calories / 4)
    fat_g = int(fat_calories / 9)
    
    return {
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g
    }

def get_meal_suggestions(calories: int, protein_g: int, carbs_g: int, fat_g: int) -> List[Dict[str, Any]]:
    """Generate sample meal suggestions"""
    
    # Simple meal database (in production, this would be much more comprehensive)
    meal_templates = {
        "breakfast": [
            {
                "name": "Oatmeal with Berries and Protein Powder",
                "calories_per_100g": 150,
                "protein_per_100g": 12,
                "carbs_per_100g": 25,
                "fat_per_100g": 3,
                "ingredients": ["Oats", "Mixed berries", "Protein powder", "Almond milk"]
            },
            {
                "name": "Greek Yogurt Parfait",
                "calories_per_100g": 120,
                "protein_per_100g": 15,
                "carbs_per_100g": 12,
                "fat_per_100g": 2,
                "ingredients": ["Greek yogurt", "Granola", "Fresh fruit", "Honey"]
            }
        ],
        "lunch": [
            {
                "name": "Grilled Chicken Salad",
                "calories_per_100g": 180,
                "protein_per_100g": 25,
                "carbs_per_100g": 8,
                "fat_per_100g": 6,
                "ingredients": ["Chicken breast", "Mixed greens", "Cherry tomatoes", "Olive oil dressing"]
            },
            {
                "name": "Quinoa Buddha Bowl",
                "calories_per_100g": 160,
                "protein_per_100g": 8,
                "carbs_per_100g": 28,
                "fat_per_100g": 4,
                "ingredients": ["Quinoa", "Roasted vegetables", "Chickpeas", "Tahini dressing"]
            }
        ],
        "dinner": [
            {
                "name": "Baked Salmon with Sweet Potato",
                "calories_per_100g": 200,
                "protein_per_100g": 22,
                "carbs_per_100g": 15,
                "fat_per_100g": 8,
                "ingredients": ["Salmon fillet", "Sweet potato", "Asparagus", "Olive oil"]
            },
            {
                "name": "Lean Beef Stir-fry",
                "calories_per_100g": 190,
                "protein_per_100g": 20,
                "carbs_per_100g": 12,
                "fat_per_100g": 7,
                "ingredients": ["Lean beef strips", "Mixed vegetables", "Brown rice", "Soy sauce"]
            }
        ],
        "snack": [
            {
                "name": "Apple with Almond Butter",
                "calories_per_100g": 160,
                "protein_per_100g": 4,
                "carbs_per_100g": 20,
                "fat_per_100g": 8,
                "ingredients": ["Apple", "Almond butter"]
            },
            {
                "name": "Protein Smoothie",
                "calories_per_100g": 140,
                "protein_per_100g": 20,
                "carbs_per_100g": 15,
                "fat_per_100g": 2,
                "ingredients": ["Protein powder", "Banana", "Spinach", "Water"]
            }
        ]
    }
    
    meals = []
    calorie_distribution = {
        "breakfast": 0.25,
        "lunch": 0.35,
        "dinner": 0.30,
        "snack": 0.10
    }
    
    for meal_type, ratio in calorie_distribution.items():
        target_calories = int(calories * ratio)
        meal_options = meal_templates[meal_type]
        
        # Select first meal option (in production, you'd have more sophisticated selection)
        selected_meal = meal_options[0].copy()
        
        # Calculate serving size to meet calorie target
        serving_multiplier = target_calories / selected_meal["calories_per_100g"]
        
        meal = {
            "meal_type": meal_type,
            "name": selected_meal["name"],
            "calories": target_calories,
            "protein_g": int(selected_meal["protein_per_100g"] * serving_multiplier),
            "carbs_g": int(selected_meal["carbs_per_100g"] * serving_multiplier),
            "fat_g": int(selected_meal["fat_per_100g"] * serving_multiplier),
            "ingredients": selected_meal["ingredients"]
        }
        meals.append(meal)
    
    return meals

def generate_nutrition_plan(
    user_data: Dict[str, Any],
    image_analysis: Optional[Dict[str, Any]],
    goal: str,
    activity_level: str = "moderate"
) -> Dict[str, Any]:
    """Generate personalized nutrition plan"""
    
    # Calculate BMR and TDEE
    bmr = calculate_bmr_harris_benedict(
        weight_kg=user_data["weight"],
        height_cm=user_data["height"],
        age=user_data["age"],
        sex=user_data["sex"]
    )
    
    tdee = calculate_tdee(bmr, activity_level)
    
    # Adjust calories based on goal
    if goal == "lose_fat":
        target_calories = int(tdee * 0.8)  # 20% deficit
    elif goal == "gain_muscle":
        target_calories = int(tdee * 1.15)  # 15% surplus
    elif goal == "recomposition":
        target_calories = int(tdee)  # Maintenance
    else:  # maintenance
        target_calories = int(tdee)
    
    # Calculate macros
    macros = calculate_macros(target_calories, goal)
    
    # Generate meal suggestions
    meals = get_meal_suggestions(
        target_calories,
        macros["protein_g"],
        macros["carbs_g"],
        macros["fat_g"]
    )
    
    return {
        "daily_targets": {
            "calories": target_calories,
            "protein_g": macros["protein_g"],
            "carbs_g": macros["carbs_g"],
            "fat_g": macros["fat_g"]
        },
        "bmr": int(bmr),
        "tdee": int(tdee),
        "meal_suggestions": meals,
        "hydration_target_ml": user_data["weight"] * 35,  # 35ml per kg body weight
        "notes": [
            f"Eat {macros['protein_g']}g protein daily to support your {goal} goal",
            "Spread protein intake across all meals",
            "Stay hydrated with at least 8 glasses of water daily",
            "Adjust portions based on hunger and energy levels"
        ]
    }