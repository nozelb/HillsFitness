# backend/test_vision_simple.py
"""
Simple test runner for quick vision pipeline testing
Usage: python test_vision_simple.py [image_path]
"""

import sys
import os
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from services.vision_pipeline import EnhancedVisionPipeline
    print("✅ Vision pipeline imported successfully")
except ImportError as e:
    print(f"❌ Failed to import vision pipeline: {e}")
    print("Make sure you're running from the backend directory and have installed requirements.txt")
    sys.exit(1)

def test_with_image(image_path: str):
    """Test the vision pipeline with a specific image"""
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    print(f"📸 Testing with image: {image_path}")
    
    try:
        # Initialize pipeline
        pipeline = EnhancedVisionPipeline()
        print("✅ Pipeline initialized")
        
        # Process image
        print("🔄 Processing image...")
        start_time = time.time()
        
        result = pipeline.process_image(
            image_path=image_path,
            user_height_cm=175.0,  # Default height
            user_weight_kg=75.0,   # Default weight  
            user_sex="male"        # Default sex
        )
        
        processing_time = time.time() - start_time
        
        # Display results
        print(f"\n📊 Results (processed in {processing_time:.2f}s):")
        print("=" * 40)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            print(f"   Error type: {result.get('error_type', 'Unknown')}")
            return False
        
        print(f"🎯 Image Quality: {result.get('imageQuality', 'N/A'):.2f}")
        print(f"📈 Body Fat Estimate: {result.get('bf_estimate', 'N/A')}%")
        print(f"🔍 Confidence Level: {result.get('confidence', 'N/A')}")
        
        # Anthropometrics
        anthro = result.get('anthro', {})
        if anthro:
            print(f"\n📏 Body Measurements:")
            for measurement, value in anthro.items():
                print(f"   {measurement}: {value:.1f}")
        
        # Posture alerts
        pose_alerts = result.get('poseAlerts', [])
        if pose_alerts:
            print(f"\n⚠️  Posture Alerts:")
            for alert in pose_alerts:
                print(f"   - {alert.replace('_', ' ').title()}")
        else:
            print(f"\n✅ No posture issues detected")
        
        # Waist-to-hip ratio
        whr = result.get('waist_to_hip_ratio')
        if whr:
            print(f"\n📐 Waist-to-Hip Ratio: {whr:.3f}")
        
        print(f"\n🕒 Analysis Timestamp: {result.get('analysis_timestamp', 'N/A')}")
        print(f"🔖 Version: {result.get('version', 'N/A')}")
        
        # Save results to file
        output_file = f"vision_result_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_sample_data():
    """Test with generated sample data when no image provided"""
    print("📸 No image provided, creating sample test image...")
    
    try:
        import cv2
        import numpy as np
        
        # Create a simple test image
        img = np.zeros((480, 640, 3), dtype=np.uint8) + 50
        
        # Draw a simple person-like figure
        cv2.rectangle(img, (280, 180), (360, 380), (100, 100, 100), -1)  # Torso
        cv2.circle(img, (320, 140), 35, (120, 120, 120), -1)  # Head
        cv2.rectangle(img, (250, 200), (280, 280), (90, 90, 90), -1)   # Left arm
        cv2.rectangle(img, (360, 200), (390, 280), (90, 90, 90), -1)   # Right arm
        cv2.rectangle(img, (300, 380), (320, 450), (80, 80, 80), -1)   # Left leg
        cv2.rectangle(img, (320, 380), (340, 450), (80, 80, 80), -1)   # Right leg
        
        # Save temporary image
        temp_path = "temp_test_image.jpg"
        cv2.imwrite(temp_path, img)
        print(f"✅ Created sample image: {temp_path}")
        
        # Test with sample image
        success = test_with_image(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"🧹 Cleaned up temporary image")
        
        return success
        
    except ImportError:
        print("❌ OpenCV not available, cannot create sample image")
        print("Please provide an image path or install opencv-python")
        return False

def main():
    """Main function"""
    print("🔍 Enhanced Vision Pipeline - Quick Test")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Use provided image path
        image_path = sys.argv[1]
        success = test_with_image(image_path)
    else:
        # Use sample data
        success = test_with_sample_data()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print("\nNext steps:")
        print("1. Try with your own images")
        print("2. Adjust user parameters (height, weight, sex)")
        print("3. Check the generated JSON output")
        print("4. Try running with a different image")
        print("5. Check system dependencies (OpenCV, MediaPipe)")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) Test with different image qualities")
    else:
        print(f"\n❌ Test failed. Check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Ensure you have installed requirements.txt")
        print("2. Check that MediaPipe is properly installed")
        print("3. Verify image file exists and is readable")
        print("4.