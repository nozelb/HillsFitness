import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Tuple, Optional, Any
import math
import os
from PIL import Image
import io

class ImageAnalysisService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
    def analyze_physique(self, image_path: str) -> Dict[str, float]:
        """Main method to analyze physique from image"""
        try:
            # Load and preprocess image
            image = self._load_image(image_path)
            if image is None:
                return self._get_default_measurements()
            
            # Detect pose landmarks
            landmarks = self._detect_pose_landmarks(image)
            if landmarks is None:
                return self._get_default_measurements()
            
            # Extract measurements
            measurements = self._calculate_measurements(landmarks, image.shape)
            
            # Estimate body fat
            body_fat = self._estimate_body_fat(measurements)
            measurements['body_fat_estimate'] = body_fat
            
            # Add confidence score
            measurements['confidence_score'] = self._calculate_confidence(landmarks)
            
            return measurements
            
        except Exception as e:
            print(f"Error in physique analysis: {e}")
            return self._get_default_measurements()
    
    def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load and validate image"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not load image")
            
            # Resize if too large
            max_dimension = 1920
            height, width = image.shape[:2]
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            return image
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def _detect_pose_landmarks(self, image: np.ndarray) -> Optional[Any]:
        """Detect pose landmarks using MediaPipe"""
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            with self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.5
            ) as pose:
                results = pose.process(image_rgb)
                
                if results.pose_landmarks:
                    return results.pose_landmarks.landmark
                return None
                
        except Exception as e:
            print(f"Error detecting pose: {e}")
            return None
    
    def _calculate_measurements(self, landmarks: Any, image_shape: Tuple[int, int]) -> Dict[str, float]:
        """Calculate body measurements from landmarks"""
        height, width = image_shape[:2]
        
        # Get key landmarks
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Convert to pixel coordinates
        def to_pixels(landmark):
            return (landmark.x * width, landmark.y * height)
        
        # Calculate distances
        shoulder_width = self._calculate_distance(
            to_pixels(left_shoulder), 
            to_pixels(right_shoulder)
        )
        
        hip_width = self._calculate_distance(
            to_pixels(left_hip), 
            to_pixels(right_hip)
        )
        
        # Estimate height from pose
        left_height = self._calculate_distance(
            to_pixels(left_shoulder),
            to_pixels(left_ankle)
        )
        right_height = self._calculate_distance(
            to_pixels(right_shoulder),
            to_pixels(right_ankle)
        )
        avg_height = (left_height + right_height) / 2
        
        # Convert pixels to cm (rough estimation)
        # Assuming average shoulder width is ~45cm
        pixel_to_cm_ratio = 45 / shoulder_width if shoulder_width > 0 else 0.3
        
        return {
            "shoulder_cm": round(shoulder_width * pixel_to_cm_ratio, 1),
            "waist_cm": round(hip_width * pixel_to_cm_ratio * 0.8, 1),  # Waist ~80% of hip
            "hip_cm": round(hip_width * pixel_to_cm_ratio, 1),
            "estimated_height_cm": round(avg_height * pixel_to_cm_ratio * 1.1, 1)
        }
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _estimate_body_fat(self, measurements: Dict[str, float]) -> float:
        """Estimate body fat percentage based on measurements"""
        # Simplified estimation based on waist-to-hip ratio
        waist = measurements.get("waist_cm", 80)
        hip = measurements.get("hip_cm", 90)
        
        if hip > 0:
            whr = waist / hip
            # Very rough estimation
            if whr < 0.85:
                return 15.0
            elif whr < 0.95:
                return 20.0
            else:
                return 25.0
        return 18.0
    
    def _calculate_confidence(self, landmarks: Any) -> float:
        """Calculate confidence score based on landmark visibility"""
        if not landmarks:
            return 0.0
        
        # Check visibility of key landmarks
        key_landmarks = [
            self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            self.mp_pose.PoseLandmark.LEFT_HIP,
            self.mp_pose.PoseLandmark.RIGHT_HIP
        ]
        
        visibility_sum = sum(
            landmarks[landmark.value].visibility 
            for landmark in key_landmarks
        )
        
        return min(visibility_sum / len(key_landmarks), 1.0)
    
    def _get_default_measurements(self) -> Dict[str, float]:
        """Return default measurements when analysis fails"""
        return {
            "waist_cm": 80.0,
            "hip_cm": 90.0,
            "shoulder_cm": 45.0,
            "body_fat_estimate": 18.0,
            "confidence_score": 0.2
        }
    
    def save_annotated_image(self, image_path: str, output_path: str) -> bool:
        """Save image with pose landmarks drawn"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            with self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=0.5
            ) as pose:
                results = pose.process(image_rgb)
                
                if results.pose_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image, 
                        results.pose_landmarks, 
                        self.mp_pose.POSE_CONNECTIONS
                    )
                
                cv2.imwrite(output_path, image)
                return True
                
        except Exception as e:
            print(f"Error saving annotated image: {e}")
            return False