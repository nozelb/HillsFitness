import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Tuple, Optional
import math

# Initialize MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def estimate_body_measurements(landmarks, image_shape: Tuple[int, int]) -> Dict[str, float]:
    """
    Estimate body measurements from pose landmarks
    This is a simplified approach - in production, you'd want more sophisticated algorithms
    """
    height, width = image_shape[:2]
    
    # Get key landmarks
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    
    # Convert normalized coordinates to pixel coordinates
    left_shoulder_pixels = (left_shoulder.x * width, left_shoulder.y * height)
    right_shoulder_pixels = (right_shoulder.x * width, right_shoulder.y * height)
    left_hip_pixels = (left_hip.x * width, left_hip.y * height)
    right_hip_pixels = (right_hip.x * width, right_hip.y * height)
    
    # Calculate measurements (these are rough estimates)
    shoulder_width_pixels = calculate_distance(left_shoulder_pixels, right_shoulder_pixels)
    hip_width_pixels = calculate_distance(left_hip_pixels, right_hip_pixels)
    
    # Rough conversion from pixels to cm (assuming average human proportions)
    # This would need calibration in a real application
    pixel_to_cm_ratio = 0.3  # This is a rough estimate
    
    shoulder_width_cm = shoulder_width_pixels * pixel_to_cm_ratio
    hip_width_cm = hip_width_pixels * pixel_to_cm_ratio
    
    # Estimate waist (roughly 80% of hip width for average person)
    waist_cm = hip_width_cm * 0.8
    
    return {
        "shoulder_cm": shoulder_width_cm,
        "waist_cm": waist_cm,
        "hip_cm": hip_width_cm
    }

def estimate_body_fat_us_navy(waist_cm: float, neck_cm: float, height_cm: float, 
                             sex: str, hip_cm: Optional[float] = None) -> float:
    """
    Estimate body fat percentage using US Navy method
    """
    if sex.lower() == "male":
        # Male formula: 86.010 * log10(abdomen - neck) - 70.041 * log10(height) + 36.76
        if waist_cm <= 0 or neck_cm <= 0 or height_cm <= 0:
            return 15.0  # Default estimate
        body_fat = 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
    else:
        # Female formula needs hip measurement
        if not hip_cm or waist_cm <= 0 or neck_cm <= 0 or height_cm <= 0 or hip_cm <= 0:
            return 20.0  # Default estimate
        body_fat = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 78.387
    
    # Clamp to reasonable range
    return max(5.0, min(50.0, body_fat))

def analyze_physique_from_image(image_path: str) -> Dict[str, float]:
    """
    Analyze physique from uploaded image using MediaPipe Pose
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Could not load image")
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Initialize pose detection
        with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        ) as pose:
            
            # Process image
            results = pose.process(image_rgb)
            
            if not results.pose_landmarks:
                # Fallback to basic estimates if pose detection fails
                return {
                    "waist_cm": 80.0,
                    "hip_cm": 90.0,
                    "shoulder_cm": 45.0,
                    "body_fat_estimate": 18.0,
                    "confidence_score": 0.3
                }
            
            # Extract measurements
            measurements = estimate_body_measurements(
                results.pose_landmarks.landmark, 
                image.shape
            )
            
            # Estimate neck (rough approximation)
            neck_cm = measurements["shoulder_cm"] * 0.3
            
            # Estimate body fat using US Navy method
            # We'll assume average height of 170cm if not provided
            body_fat = estimate_body_fat_us_navy(
                waist_cm=measurements["waist_cm"],
                neck_cm=neck_cm,
                height_cm=170.0,  # Default height
                sex="male",  # Default sex
                hip_cm=measurements.get("hip_cm")
            )
            
            return {
                "waist_cm": round(measurements["waist_cm"], 1),
                "hip_cm": round(measurements.get("hip_cm", 0), 1),
                "shoulder_cm": round(measurements["shoulder_cm"], 1),
                "body_fat_estimate": round(body_fat, 1),
                "confidence_score": 0.8  # High confidence if pose detected
            }
            
    except Exception as e:
        # Return default estimates if analysis fails
        return {
            "waist_cm": 80.0,
            "hip_cm": 90.0,
            "shoulder_cm": 45.0,
            "body_fat_estimate": 18.0,
            "confidence_score": 0.2
        }