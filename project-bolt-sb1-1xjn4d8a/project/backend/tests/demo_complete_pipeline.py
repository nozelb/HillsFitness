# backend/demo_complete_pipeline.py
"""
Complete end-to-end demonstration of the Enhanced Vision Pipeline
This script shows the full workflow from image upload to plan generation
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def create_demo_user_data():
    """Create sample user data for testing"""
    return {
        "user_id": "demo_user_123",
        "email": "demo@example.com",
        "full_name": "Demo User",
        "physical_data": {
            "weight": 75.0,
            "height": 175.0,
            "age": 28,
            "sex": "male"
        },
        "fitness_goal": "lose_fat",
        "activity_level": "moderate",
        "experience_level": "intermediate",
        "days_per_week": 4
    }

def create_sample_image():
    """Create a sample person image for testing"""
    try:
        import cv2
        import numpy as np
        
        print("🎨 Creating sample person image...")
        
        # Create a more realistic person image
        img = np.zeros((640, 480, 3), dtype=np.uint8) + 80  # Light gray background
        
        # Person silhouette (front view)
        # Head
        cv2.circle(img, (240, 100), 40, (150, 130, 120), -1)
        
        # Neck
        cv2.rectangle(img, (230, 135), (250, 160), (140, 120, 110), -1)
        
        # Torso
        cv2.rectangle(img, (200, 160), (280, 320), (130, 110, 100), -1)
        
        # Arms
        cv2.rectangle(img, (160, 180), (200, 280), (120, 100, 90), -1)  # Left arm
        cv2.rectangle(img, (280, 180), (320, 280), (120, 100, 90), -1)  # Right arm
        
        # Legs  
        cv2.rectangle(img, (210, 320), (235, 500), (110, 90, 80), -1)   # Left leg
        cv2.rectangle(img, (245, 320), (270, 500), (110, 90, 80), -1)   # Right leg
        
        # Add some noise for realism
        noise = np.random.randint(0, 30, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        
        # Add slight blur for realism
        img = cv2.GaussianBlur(img, (3, 3), 0)
        
        # Save the image
        demo_image_path = "demo_person.jpg"
        cv2.imwrite(demo_image_path, img)
        
        print(f"✅ Sample image created: {demo_image_path}")
        return demo_image_path
        
    except ImportError:
        print("❌ OpenCV not available - please provide your own image")
        return None

async def demo_vision_analysis(image_path: str, user_data: Dict[str, Any]):
    """Demonstrate the vision analysis process"""
    print(f"\n🔍 STAGE 1: Vision Analysis")
    print("=" * 40)
    
    try:
        from services.vision_pipeline import EnhancedVisionPipeline
        
        # Initialize pipeline
        pipeline = EnhancedVisionPipeline()
        print("✅ Vision pipeline initialized")
        
        # Extract user parameters
        physical_data = user_data["physical_data"]
        
        print(f"📸 Processing image: {image_path}")
        print(f"👤 User: {physical_data['height']}cm, {physical_data['weight']}kg, {physical_data['sex']}")
        
        # Process image
        start_time = time.time()
        vision_result = pipeline.process_image(
            image_path=image_path,
            user_height_cm=physical_data["height"],
            user_weight_kg=physical_data["weight"],
            user_sex=physical_data["sex"]
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing completed in {processing_time:.2f}s")
        
        # Display vision results
        if "error" in vision_result:
            print(f"❌ Vision analysis failed: {vision_result['error']}")
            return None
        
        print(f"\n📊 Vision Analysis Results:")
        print(f"   🎯 Image Quality: {vision_result['imageQuality']:.2f}")
        print(f"   📈 Body Fat Estimate: {vision_result['bf_estimate']}%")
        print(f"   🔍 Confidence: {vision_result['confidence']}")
        
        # Show anthropometrics
        anthro = vision_result['anthro']
        print(f"\n📏 Body Measurements:")
        for measurement, value in anthro.items():
            print(f"   {measurement.replace('_', ' ').title()}: {value:.1f}cm")
        
        # Show posture alerts
        pose_alerts = vision_result['poseAlerts']
        if pose_alerts:
            print(f"\n⚠️  Posture Issues Detected:")
            for alert in pose_alerts:
                print(f"   - {alert.replace('_', ' ').title()}")
        else:
            print(f"\n✅ No significant posture issues detected")
        
        return vision_result
        
    except Exception as e:
        print(f"❌ Vision analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_plan_generation(user_data: Dict[str, Any], vision_metrics: Dict[str, Any]):
    """Demonstrate plan generation with vision metrics"""
    print(f"\n🏋️ STAGE 2: Plan Generation with Vision Integration")
    print("=" * 50)
    
    try:
        # Simulate the enhanced plan generation
        print("🧠 Generating personalized fitness plan...")
        
        # Base plan parameters
        goal = user_data["fitness_goal"]
        days = user_data["days_per_week"]
        activity = user_data["activity_level"]
        experience = user_data["experience_level"]
        
        print(f"📋 Plan Parameters:")
        print(f"   Goal: {goal.replace('_', ' ').title()}")
        print(f"   Training Days: {days}/week")
        print(f"   Activity Level: {activity.title()}")
        print(f"   Experience: {experience.title()}")
        
        # Vision-based adjustments
        vision_adjustments = []
        
        # Check for posture issues
        pose_alerts = vision_metrics.get('poseAlerts', [])
        if 'rounded_shoulders' in pose_alerts:
            vision_adjustments.append("Added corrective exercises for rounded shoulders")
        if 'anterior_pelvic_tilt' in pose_alerts:
            vision_adjustments.append("Included core stability work for pelvic alignment")
        if 'forward_head' in pose_alerts:
            vision_adjustments.append("Added neck strengthening exercises")
        
        # Body composition adjustments
        bf_estimate = vision_metrics.get('bf_estimate', 20)
        confidence = vision_metrics.get('confidence', 'medium')
        
        if bf_estimate > 25:
            vision_adjustments.append(f"Increased protein target based on {bf_estimate}% body fat")
            vision_adjustments.append("Applied moderate calorie deficit for fat loss")
        elif bf_estimate < 12:
            vision_adjustments.append(f"Conservative approach for lean physique ({bf_estimate}% BF)")
        
        # Anthropometric adjustments  
        anthro = vision_metrics.get('anthro', {})
        hip_cm = anthro.get('hip_cm', 90)
        if hip_cm > 95:
            vision_adjustments.append("Modified squat mechanics for longer limb proportions")
        
        # Generate sample workout plan
        workout_plan = generate_sample_workout(pose_alerts, anthro)
        
        # Generate sample nutrition plan
        nutrition_plan = generate_sample_nutrition(user_data["physical_data"], bf_estimate, goal)
        
        print(f"\n💪 Enhanced Workout Plan:")
        for i, exercise in enumerate(workout_plan, 1):
            corrective = " (Corrective)" if exercise.get("corrective") else ""
            print(f"   {i}. {exercise['name']}{corrective}")
            print(f"      {exercise['sets']} sets × {exercise['reps']} reps")
            if exercise.get("reason"):
                print(f"      💡 {exercise['reason']}")
        
        print(f"\n🍎 Nutrition Targets:")
        print(f"   📊 Daily Calories: {nutrition_plan['calories']}")
        print(f"   🥩 Protein: {nutrition_plan['protein_g']}g")
        print(f"   🍞 Carbs: {nutrition_plan['carbs_g']}g") 
        print(f"   🥑 Fat: {nutrition_plan['fat_g']}g")
        
        print(f"\n🎯 Vision-Based Adjustments:")
        if vision_adjustments:
            for adjustment in vision_adjustments:
                print(f"   ✨ {adjustment}")
        else:
            print(f"   ✅ Standard evidence-based plan - no adjustments needed")
        
        print(f"\n📝 Rationale:")
        rationale = f"This {days}-day program is tailored for {goal.replace('_', ' ')} based on your {experience} experience level. "
        if pose_alerts:
            rationale += f"We've included corrective exercises for your posture ({', '.join(pose_alerts).replace('_', ' ')}). "
        rationale += f"Your estimated body fat ({bf_estimate}% with {confidence} confidence) guided the nutrition targets."
        print(f"   {rationale}")
        
        return {
            "workout_plan": workout_plan,
            "nutrition_plan": nutrition_plan,
            "vision_adjustments": vision_adjustments,
            "rationale": rationale
        }
        
    except Exception as e:
        print(f"❌ Plan generation failed: {e}")
        return None

def generate_sample_workout(pose_alerts, anthro):
    """Generate a sample workout with vision adjustments"""
    exercises = []
    
    # Add corrective exercises first
    if 'rounded_shoulders' in pose_alerts:
        exercises.append({
            "name": "Thoracic Spine Opener",
            "sets": 2,
            "reps": "8-10",
            "corrective": True,
            "reason": "Mobility drill for rounded shoulders"
        })
        exercises.append({
            "name": "Face Pulls",
            "sets": 3,
            "reps": "12-15",
            "corrective": True,
            "reason": "Strengthen posterior chain"
        })
    
    if 'anterior_pelvic_tilt' in pose_alerts:
        exercises.append({
            "name": "Dead Bug",
            "sets": 2,
            "reps": "6 each side",
            "corrective": True,
            "reason": "Core stability for pelvic alignment"
        })
    
    # Main exercises
    squat_name = "Squats"
    hip_cm = anthro.get('hip_cm', 90)
    if hip_cm > 95:
        squat_name = "Goblet Squats"
        squat_reason = "Better mechanics for longer proportions"
    else:
        squat_reason = "Fundamental movement pattern"
    
    exercises.extend([
        {
            "name": squat_name,
            "sets": 3,
            "reps": "8-12",
            "reason": squat_reason
        },
        {
            "name": "Push-ups",
            "sets": 3,
            "reps": "8-15"
        },
        {
            "name": "Romanian Deadlifts",
            "sets": 3,
            "reps": "8-10"
        },
        {
            "name": "Planks",
            "sets": 2,
            "reps": "30-60 seconds"
        }
    ])
    
    return exercises

def generate_sample_nutrition(physical_data, bf_estimate, goal):
    """Generate sample nutrition targets"""
    weight = physical_data["weight"]
    height = physical_data["height"]
    age = physical_data["age"]
    sex = physical_data["sex"]
    
    # Calculate BMR
    if sex.lower() == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Activity multiplier (moderate)
    tdee = bmr * 1.55
    
    # Goal adjustments
    goal_adjustments = {
        "lose_fat": -400,
        "gain_muscle": 300,
        "recomposition": -200,
        "maintenance": 0
    }
    
    target_calories = tdee + goal_adjustments.get(goal, 0)
    
    # Body fat adjustments
    if bf_estimate > 25:
        target_calories -= 100  # Larger deficit
        protein_multiplier = 1.3
    elif bf_estimate < 12:
        target_calories += 100  # Conservative
        protein_multiplier = 1.1
    else:
        protein_multiplier = 1.2
    
    # Macros
    protein_g = weight * 2.2 * protein_multiplier
    fat_g = target_calories * 0.27 / 9
    carbs_g = (target_calories - (protein_g * 4) - (fat_g * 9)) / 4
    
    return {
        "calories": round(target_calories),
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1)
    }

def save_demo_results(user_data, vision_metrics, plan_data):
    """Save complete demo results to file"""
    demo_results = {
        "timestamp": time.time(),
        "user_data": user_data,
        "vision_analysis": vision_metrics,
        "generated_plan": plan_data,
        "pipeline_version": "2.1.0"
    }
    
    filename = f"demo_results_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(demo_results, f, indent=2)
    
    print(f"\n💾 Complete demo results saved to: {filename}")
    return filename

async def main():
    """Main demo function"""
    print("🚀 Enhanced Vision Pipeline - Complete Demo")
    print("=" * 60)
    print("This demo shows the full workflow from image analysis to plan generation")
    print()
    
    try:
        # Create demo user data
        user_data = create_demo_user_data()
        print(f"👤 Demo User: {user_data['full_name']} ({user_data['physical_data']['height']}cm, {user_data['physical_data']['weight']}kg)")
        
        # Create or use existing image
        if len(sys.argv) > 1:
            image_path = sys.argv[1]
            if not os.path.exists(image_path):
                print(f"❌ Image not found: {image_path}")
                return 1
        else:
            image_path = create_sample_image()
            if not image_path:
                return 1
        
        # Run vision analysis
        vision_metrics = await demo_vision_analysis(image_path, user_data)
        if not vision_metrics:
            return 1
        
        # Generate enhanced plan
        plan_data = demo_plan_generation(user_data, vision_metrics)
        if not plan_data:
            return 1
        
        # Save results
        results_file = save_demo_results(user_data, vision_metrics, plan_data)
        
        print(f"\n🎉 Demo Completed Successfully!")
        print(f"\nThis demonstrates how the enhanced vision pipeline:")
        print(f"✅ Analyzes body composition and posture from photos")
        print(f"✅ Generates personalized corrective exercises")
        print(f"✅ Adjusts nutrition based on body fat estimates")
        print(f"✅ Explains why specific recommendations were made")
        print(f"✅ Adapts exercise selection to body proportions")
        
        print(f"\n📋 Next Steps:")
        print(f"1. Review the detailed results in {results_file}")
        print(f"2. Test with your own images")
        print(f"3. Deploy the full system with Docker Compose")
        print(f"4. Monitor user feedback and accuracy")
        
        # Cleanup demo image if created
        if len(sys.argv) == 1 and os.path.exists("demo_person.jpg"):
            os.remove("demo_person.jpg")
            print(f"\n🧹 Cleaned up demo image")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⏸️  Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(f"📸 Using provided image: {sys.argv[1]}")
    else:
        print(f"📸 Will create sample image for demo")
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)