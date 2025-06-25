# utils/constants.py - Exercise database and safety limits

EXERCISE_DATABASE = {
    "chest": [
                {
            "name": "Push-ups",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Incline Push-ups", "Knee Push-ups"],
            "notes": "Great foundation exercise",
            "safety_notes": "Keep core tight, full range of motion"
        },
        {
            "name": "Dumbbell Bench Press",
            "equipment": ["dumbbells", "bench"],
            "difficulty": "beginner",
            "substitutions": ["Barbell Bench Press", "Machine Press"],
            "notes": "Control the weight on the way down"
        },
        {
            "name": "Incline Dumbbell Press",
            "equipment": ["dumbbells", "incline_bench"],
            "difficulty": "intermediate",
            "substitutions": ["Incline Barbell Press", "Push-ups"],
            "notes": "Targets upper chest"
        },
        {
            "name": "Dips",
            "equipment": ["dip_bars"],
            "difficulty": "intermediate",
            "substitutions": ["Tricep Dips", "Close-grip Push-ups"],
            "notes": "Lean forward for chest emphasis"
        },
        {
            "name": "Chest Flyes",
            "equipment": ["dumbbells", "bench"],
            "difficulty": "intermediate",
            "substitutions": ["Cable Flyes", "Pec Deck"],
            "notes": "Focus on squeeze at the top"
        }
    ],
    "back": [
        {
            "name": "Pull-ups",
            "equipment": ["pull_up_bar"],
            "difficulty": "intermediate",
            "substitutions": ["Lat Pulldown", "Assisted Pull-ups"],
            "notes": "Full range of motion, control the descent"
        },
        {
            "name": "Bent-over Rows",
            "equipment": ["barbell"],
            "difficulty": "intermediate",
            "substitutions": ["Dumbbell Rows", "Cable Rows"],
            "notes": "Keep back straight, pull to lower chest"
        },
        {
            "name": "Lat Pulldown",
            "equipment": ["cable_machine"],
            "difficulty": "beginner",
            "substitutions": ["Pull-ups", "Resistance Band Pulldowns"],
            "notes": "Pull to upper chest, squeeze shoulder blades"
        },
        {
            "name": "Deadlifts",
            "equipment": ["barbell"],
            "difficulty": "advanced",
            "substitutions": ["Romanian Deadlifts", "Trap Bar Deadlifts"],
            "notes": "Keep bar close to body, drive through heels",
            "safety_notes": "Master form before adding weight"
        },
        {
            "name": "Single-arm Dumbbell Row",
            "equipment": ["dumbbell", "bench"],
            "difficulty": "beginner",
            "substitutions": ["Cable Rows", "Resistance Band Rows"],
            "notes": "Support yourself with opposite arm"
        }
    ],
    "shoulders": [
        {
            "name": "Overhead Press",
            "equipment": ["dumbbells"],
            "difficulty": "beginner",
            "substitutions": ["Military Press", "Machine Press"],
            "notes": "Press straight up, keep core tight"
        },
        {
            "name": "Lateral Raises",
            "equipment": ["dumbbells"],
            "difficulty": "beginner",
            "substitutions": ["Cable Lateral Raises", "Resistance Band Raises"],
            "notes": "Control the weight, slight bend in elbows"
        },
        {
            "name": "Face Pulls",
            "equipment": ["cable_machine"],
            "difficulty": "beginner",
            "substitutions": ["Resistance Band Face Pulls", "Reverse Flyes"],
            "notes": "Great for rear delts and posture"
        },
        {
            "name": "Pike Push-ups",
            "equipment": ["bodyweight"],
            "difficulty": "intermediate",
            "substitutions": ["Handstand Push-ups", "Overhead Press"],
            "notes": "Feet elevated, press up and back"
        },
        {
            "name": "Arnold Press",
            "equipment": ["dumbbells"],
            "difficulty": "intermediate",
            "substitutions": ["Regular Shoulder Press", "Machine Press"],
            "notes": "Rotate palms during the movement"
        }
    ],
    "triceps": [
        {
            "name": "Tricep Dips",
            "equipment": ["bodyweight", "bench"],
            "difficulty": "beginner",
            "substitutions": ["Assisted Dips", "Close-grip Push-ups"],
            "notes": "Keep elbows close to body"
        },
        {
            "name": "Close-grip Push-ups",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Diamond Push-ups", "Tricep Dips"],
            "notes": "Hands in diamond shape"
        },
        {
            "name": "Overhead Tricep Extension",
            "equipment": ["dumbbell"],
            "difficulty": "beginner",
            "substitutions": ["Cable Tricep Extension", "Tricep Dips"],
            "notes": "Keep elbows stationary"
        },
        {
            "name": "Tricep Pushdowns",
            "equipment": ["cable_machine"],
            "difficulty": "beginner",
            "substitutions": ["Overhead Extension", "Close-grip Push-ups"],
            "notes": "Keep elbows at sides"
        }
    ],
    "biceps": [
        {
            "name": "Bicep Curls",
            "equipment": ["dumbbells"],
            "difficulty": "beginner",
            "substitutions": ["Barbell Curls", "Cable Curls"],
            "notes": "Control the weight on the way down"
        },
        {
            "name": "Hammer Curls",
            "equipment": ["dumbbells"],
            "difficulty": "beginner",
            "substitutions": ["Cable Hammer Curls", "Resistance Band Curls"],
            "notes": "Neutral grip, targets brachialis"
        },
        {
            "name": "Chin-ups",
            "equipment": ["pull_up_bar"],
            "difficulty": "intermediate",
            "substitutions": ["Assisted Chin-ups", "Cable Curls"],
            "notes": "Underhand grip, pull chest to bar"
        },
        {
            "name": "21s",
            "equipment": ["barbell"],
            "difficulty": "intermediate",
            "substitutions": ["Regular Curls", "Cable Curls"],
            "notes": "7 bottom half, 7 top half, 7 full reps"
        }
    ],
    "legs": [
        {
            "name": "Bodyweight Squats",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Goblet Squats", "Wall Sits"],
            "notes": "Keep knees in line with toes"
        },
        {
            "name": "Goblet Squats",
            "equipment": ["dumbbell"],
            "difficulty": "beginner",
            "substitutions": ["Bodyweight Squats", "Front Squats"],
            "notes": "Hold weight at chest level"
        },
        {
            "name": "Lunges",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Reverse Lunges", "Step-ups"],
            "notes": "Step forward, drop back knee down"
        },
        {
            "name": "Romanian Deadlifts",
            "equipment": ["dumbbells"],
            "difficulty": "intermediate",
            "substitutions": ["Good Mornings", "Hip Hinges"],
            "notes": "Hinge at hips, feel stretch in hamstrings"
        },
        {
            "name": "Bulgarian Split Squats",
            "equipment": ["bodyweight", "bench"],
            "difficulty": "intermediate",
            "substitutions": ["Reverse Lunges", "Single-leg Squats"],
            "notes": "Rear foot elevated, most weight on front leg"
        },
        {
            "name": "Calf Raises",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Single-leg Calf Raises", "Seated Calf Raises"],
            "notes": "Rise up on toes, squeeze at the top"
        },
        {
            "name": "Wall Sits",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Squats", "Leg Press"],
            "notes": "Back against wall, thighs parallel to floor"
        }
    ],
    "core": [
        {
            "name": "Plank",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Modified Plank", "Dead Bug"],
            "notes": "Keep body in straight line"
        },
        {
            "name": "Dead Bug",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Bird Dog", "Plank"],
            "notes": "Opposite arm and leg, keep back flat"
        },
        {
            "name": "Mountain Climbers",
            "equipment": ["bodyweight"],
            "difficulty": "intermediate",
            "substitutions": ["High Knees", "Plank"],
            "notes": "Keep hips level, alternate legs quickly"
        },
        {
            "name": "Russian Twists",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Bicycle Crunches", "Side Planks"],
            "notes": "Lean back, twist side to side"
        },
        {
            "name": "Bicycle Crunches",
            "equipment": ["bodyweight"],
            "difficulty": "beginner",
            "substitutions": ["Regular Crunches", "Russian Twists"],
            "notes": "Opposite elbow to knee"
        },
        {
            "name": "Side Plank",
            "equipment": ["bodyweight"],
            "difficulty": "intermediate",
            "substitutions": ["Modified Side Plank", "Russian Twists"],
            "notes": "Body in straight line, hold on side"
        }
    ]
}

NUTRITION_DATABASE = {
    "breakfast": [
        {
            "name": "Protein Oatmeal Bowl",
            "ingredients": ["Rolled oats", "Protein powder", "Banana", "Berries", "Almond butter"],
            "prep_time": 10,
            "tags": ["high_protein", "vegetarian"],
            "description": "Creamy oats with protein boost and fresh fruit"
        },
        {
            "name": "Greek Yogurt Parfait",
            "ingredients": ["Greek yogurt", "Granola", "Mixed berries", "Honey", "Nuts"],
            "prep_time": 5,
            "tags": ["high_protein", "vegetarian", "quick"],
            "description": "Layered yogurt with crunchy granola and fruit"
        },
        {
            "name": "Veggie Scramble",
            "ingredients": ["Eggs", "Spinach", "Bell peppers", "Onions", "Cheese", "Avocado"],
            "prep_time": 15,
            "tags": ["high_protein", "vegetarian", "low_carb"],
            "description": "Scrambled eggs packed with colorful vegetables"
        },
        {
            "name": "Protein Smoothie Bowl",
            "ingredients": ["Protein powder", "Frozen berries", "Banana", "Spinach", "Almond milk", "Granola"],
            "prep_time": 10,
            "tags": ["high_protein", "vegetarian", "quick"],
            "description": "Thick smoothie topped with crunchy granola"
        }
    ],
    "lunch": [
        {
            "name": "Grilled Chicken Salad",
            "ingredients": ["Chicken breast", "Mixed greens", "Cherry tomatoes", "Cucumber", "Olive oil", "Balsamic vinegar"],
            "prep_time": 20,
            "tags": ["high_protein", "low_carb"],
            "description": "Fresh salad with lean grilled chicken"
        },
        {
            "name": "Quinoa Buddha Bowl",
            "ingredients": ["Quinoa", "Chickpeas", "Roasted vegetables", "Tahini", "Lemon", "Spinach"],
            "prep_time": 25,
            "tags": ["vegetarian", "high_fiber", "complete_protein"],
            "description": "Nutritious bowl with plant-based protein"
        },
        {
            "name": "Turkey and Avocado Wrap",
            "ingredients": ["Whole wheat tortilla", "Turkey breast", "Avocado", "Lettuce", "Tomato", "Hummus"],
            "prep_time": 10,
            "tags": ["high_protein", "quick"],
            "description": "Protein-packed wrap with healthy fats"
        },
        {
            "name": "Salmon and Sweet Potato",
            "ingredients": ["Salmon fillet", "Sweet potato", "Broccoli", "Olive oil", "Lemon"],
            "prep_time": 30,
            "tags": ["high_protein", "omega3", "anti_inflammatory"],
            "description": "Baked salmon with roasted vegetables"
        }
    ],
    "dinner": [
        {
            "name": "Lean Beef Stir-fry",
            "ingredients": ["Lean beef", "Mixed vegetables", "Brown rice", "Soy sauce", "Ginger", "Garlic"],
            "prep_time": 25,
            "tags": ["high_protein", "high_iron"],
            "description": "Quick stir-fry with lean protein and veggies"
        },
        {
            "name": "Baked Cod with Vegetables",
            "ingredients": ["Cod fillet", "Asparagus", "Zucchini", "Olive oil", "Herbs", "Lemon"],
            "prep_time": 30,
            "tags": ["high_protein", "low_calorie", "omega3"],
            "description": "Light fish dinner with seasonal vegetables"
        },
        {
            "name": "Chicken and Rice Bowl",
            "ingredients": ["Chicken thigh", "Brown rice", "Steamed broccoli", "Carrots", "Teriyaki sauce"],
            "prep_time": 35,
            "tags": ["high_protein", "balanced"],
            "description": "Balanced meal with lean protein and complex carbs"
        },
        {
            "name": "Lentil Curry",
            "ingredients": ["Red lentils", "Coconut milk", "Spinach", "Tomatoes", "Curry spices", "Brown rice"],
            "prep_time": 40,
            "tags": ["vegetarian", "high_fiber", "plant_protein"],
            "description": "Hearty plant-based curry with complete nutrition"
        }
    ],
    "snack": [
        {
            "name": "Apple with Almond Butter",
            "ingredients": ["Apple", "Almond butter"],
            "prep_time": 2,
            "tags": ["quick", "healthy_fats", "fiber"],
            "description": "Simple snack with natural sweetness and protein"
        },
        {
            "name": "Protein Smoothie",
            "ingredients": ["Protein powder", "Banana", "Spinach", "Almond milk"],
            "prep_time": 5,
            "tags": ["high_protein", "quick", "post_workout"],
            "description": "Quick protein boost for recovery"
        },
        {
            "name": "Trail Mix",
            "ingredients": ["Mixed nuts", "Dried fruit", "Dark chocolate chips"],
            "prep_time": 1,
            "tags": ["healthy_fats", "energy", "portable"],
            "description": "Energy-dense mix for on-the-go"
        },
        {
            "name": "Cottage Cheese Bowl",
            "ingredients": ["Cottage cheese", "Berries", "Honey", "Chopped nuts"],
            "prep_time": 3,
            "tags": ["high_protein", "calcium", "quick"],
            "description": "Creamy high-protein snack with natural sweetness"
        }
    ]
}

SAFETY_LIMITS = {
    "min_calories": {
        "male": 1500,
        "female": 1200
    },
    "max_deficit": 0.25,  # Maximum 25% calorie deficit
    "min_protein_per_kg": 0.8,  # Minimum 0.8g protein per kg body weight
    "max_training_days": {
        "beginner": 4,
        "intermediate": 5,
        "advanced": 6
    },
    "progression_limits": {
        "beginner": {"volume_increase": 0.05},  # 5% per week max
        "intermediate": {"volume_increase": 0.10},  # 10% per week max
        "advanced": {"volume_increase": 0.15}  # 15% per week max
    },
    "rest_days_per_week": {
        "beginner": 3,
        "intermediate": 2,
        "advanced": 1
    }
}
