# backend/services/vision_pipeline.py
import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Optional, Tuple, Any
import math
import logging
from dataclasses import dataclass
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostureFlag(Enum):
    ROUNDED_SHOULDERS = "rounded_shoulders"
    ANTERIOR_PELVIC_TILT = "anterior_pelvic_tilt"
    FORWARD_HEAD = "forward_head"
    ASYMMETRIC_SHOULDERS = "asymmetric_shoulders"
    KNEE_VALGUS = "knee_valgus"

@dataclass
class VisionMetrics:
    """Complete vision analysis result following the specified contract"""
    pose_alerts: List[str]
    anthro: Dict[str, float]
    bf_estimate: float
    image_quality: float
    confidence_level: str = "high"  # high, medium, low
    analysis_method: str = "mediapipe_pose"

class EnhancedVisionPipeline:
    """
    Advanced vision pipeline implementing the 6-stage process:
    1. Image Quality Gate
    2. Segmentation  
    3. Pose Detection
    4. Anthropometrics
    5. Body Composition Estimate
    6. Output JSON
    """
    
    def __init__(self):
        # Initialize MediaPipe components
        self.mp_pose = mp.solutions.pose
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Quality thresholds
        self.min_quality_score = 0.7
        self.min_detection_confidence = 0.5
        
        # Anthropometric reference ratios (based on biomechanics research)
        self.anthro_ratios = {
            'waist_to_shoulder': 0.75,  # Average waist-to-shoulder ratio
            'hip_to_shoulder': 0.95,    # Average hip-to-shoulder ratio  
            'neck_to_shoulder': 0.35,   # Average neck-to-shoulder ratio
        }
        
    def process_image(self, image_path: str, user_height_cm: float, 
                     user_weight_kg: float, user_sex: str) -> Dict[str, Any]:
        """
        Main pipeline entry point - processes image through all 6 stages
        """
        try:
            # Stage 1: Image Quality Gate
            image, quality_score = self._stage1_quality_gate(image_path)
            if quality_score < self.min_quality_score:
                return self._error_response("low_quality", quality_score)
            
            # Stage 2: Segmentation
            segmented_image, mask = self._stage2_segmentation(image)
            
            # Stage 3: Pose Detection  
            landmarks, pose_results = self._stage3_pose_detection(image)
            if landmarks is None:
                return self._error_response("pose_detection_failed", quality_score)
            
            # Stage 4: Anthropometrics
            anthro_data = self._stage4_anthropometrics(landmarks, image.shape, user_height_cm)
            
            # Stage 5: Body Composition Estimate
            bf_estimate, confidence = self._stage5_body_composition(
                segmented_image, anthro_data, user_height_cm, user_weight_kg, user_sex
            )
            
            # Stage 6: Output JSON
            return self._stage6_output_json(
                pose_results, anthro_data, bf_estimate, quality_score, confidence
            )
            
        except Exception as e:
            logger.error(f"Vision pipeline error: {str(e)}")
            return self._error_response("processing_failed", 0.2)
    
    def _stage1_quality_gate(self, image_path: str) -> Tuple[np.ndarray, float]:
        """Stage 1: Reject unusable photos early"""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Could not load image")
        
        # Resize if too large (optimization)
        h, w = image.shape[:2]
        if max(h, w) > 1024:
            scale = 1024 / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h))
        
        quality_score = self._assess_image_quality(image)
        return image, quality_score
    
    def _assess_image_quality(self, image: np.ndarray) -> float:
        """Assess image quality using multiple metrics"""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Blur detection using Laplacian variance
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_quality = min(blur_score / 500.0, 1.0)  # Normalize
        
        # 2. Brightness analysis
        mean_brightness = np.mean(gray)
        brightness_quality = 1.0 - abs(mean_brightness - 128) / 128.0
        
        # 3. Contrast analysis
        contrast = gray.std()
        contrast_quality = min(contrast / 64.0, 1.0)  # Normalize
        
        # 4. Check if image is too dark or too bright
        if mean_brightness < 30 or mean_brightness > 220:
            brightness_quality *= 0.5
        
        # Weighted combination
        overall_quality = (
            blur_quality * 0.4 + 
            brightness_quality * 0.3 + 
            contrast_quality * 0.3
        )
        
        return min(overall_quality, 1.0)
    
    def _stage2_segmentation(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Stage 2: Isolate body silhouette using MediaPipe Selfie Segmentation"""
        try:
            with self.mp_selfie_segmentation.SelfieSegmentation(model_selection=1) as segmentation:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = segmentation.process(image_rgb)
                
                # Create mask
                mask = results.segmentation_mask > 0.5
                mask_3channel = np.stack([mask] * 3, axis=-1)
                
                # Apply mask to isolate body
                segmented_image = image * mask_3channel.astype(np.uint8)
                
                return segmented_image, mask.astype(np.uint8)
        except Exception as e:
            logger.warning(f"Segmentation failed: {e}, using original image")
            return image, np.ones((image.shape[0], image.shape[1]), dtype=np.uint8)
    
    def _stage3_pose_detection(self, image: np.ndarray) -> Tuple[Optional[Any], Optional[Any]]:
        """Stage 3: Joint coordinates & posture using MoveNet/MediaPipe"""
        try:
            with self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=self.min_detection_confidence
            ) as pose:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)
                
                if results.pose_landmarks:
                    return results.pose_landmarks.landmark, results
                
                return None, None
                
        except Exception as e:
            logger.error(f"Pose detection failed: {e}")
            return None, None
    
    def _stage4_anthropometrics(self, landmarks: Any, image_shape: Tuple[int, int], 
                               user_height_cm: float) -> Dict[str, float]:
        """Stage 4: Convert pixels to cm using height as scale factor"""
        height, width = image_shape[:2]
        
        # Get key anatomical landmarks
        landmark_indices = {
            'left_shoulder': self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            'right_shoulder': self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            'left_hip': self.mp_pose.PoseLandmark.LEFT_HIP,
            'right_hip': self.mp_pose.PoseLandmark.RIGHT_HIP,
            'left_knee': self.mp_pose.PoseLandmark.LEFT_KNEE,
            'right_knee': self.mp_pose.PoseLandmark.RIGHT_KNEE,
            'left_ankle': self.mp_pose.PoseLandmark.LEFT_ANKLE,
            'right_ankle': self.mp_pose.PoseLandmark.RIGHT_ANKLE,
            'nose': self.mp_pose.PoseLandmark.NOSE,
        }
        
        # Convert to pixel coordinates
        points = {}
        for name, landmark_idx in landmark_indices.items():
            landmark = landmarks[landmark_idx.value]
            points[name] = (landmark.x * width, landmark.y * height)
        
        # Calculate key distances in pixels
        shoulder_width_px = self._calculate_distance(
            points['left_shoulder'], points['right_shoulder']
        )
        
        hip_width_px = self._calculate_distance(
            points['left_hip'], points['right_hip']
        )
        
        # Calculate body height in pixels (nose to ankle)
        left_body_height_px = self._calculate_distance(
            points['nose'], points['left_ankle']
        )
        right_body_height_px = self._calculate_distance(
            points['nose'], points['right_ankle']
        )
        body_height_px = (left_body_height_px + right_body_height_px) / 2
        
        # Scale factor: user_height_cm / body_height_px
        if body_height_px > 0:
            pixel_to_cm_ratio = user_height_cm / body_height_px
        else:
            # Fallback ratio
            pixel_to_cm_ratio = 0.3
        
        # Convert measurements to centimeters
        shoulder_cm = shoulder_width_px * pixel_to_cm_ratio
        hip_cm = hip_width_px * pixel_to_cm_ratio
        
        # Estimate additional measurements using anatomical ratios
        waist_cm = shoulder_cm * self.anthro_ratios['waist_to_shoulder']
        neck_cm = shoulder_cm * self.anthro_ratios['neck_to_shoulder']
        
        # Calculate additional derived measurements
        chest_cm = shoulder_cm * 0.85  # Chest typically 85% of shoulder width
        thigh_cm = hip_cm * 0.4       # Thigh circumference estimate
        arm_cm = shoulder_cm * 0.3    # Upper arm circumference estimate
        
        return {
            'shoulder_cm': round(shoulder_cm, 1),
            'waist_cm': round(waist_cm, 1),
            'hip_cm': round(hip_cm, 1),
            'chest_cm': round(chest_cm, 1),
            'neck_cm': round(neck_cm, 1),
            'thigh_cm': round(thigh_cm, 1),
            'arm_cm': round(arm_cm, 1)
        }
    
    def _stage5_body_composition(self, segmented_image: np.ndarray, anthro_data: Dict[str, float],
                                user_height_cm: float, user_weight_kg: float, 
                                user_sex: str) -> Tuple[float, str]:
        """Stage 5: Approximate BF% & muscle mass using enhanced methods"""
        
        # Method 1: US Navy Formula (most reliable)
        navy_bf = self._calculate_navy_body_fat(
            anthro_data['waist_cm'], 
            anthro_data['neck_cm'], 
            user_height_cm, 
            user_sex, 
            anthro_data.get('hip_cm')
        )
        
        # Method 2: Visual analysis (simplified CNN simulation)
        visual_bf = self._estimate_visual_body_fat(segmented_image, user_sex)
        
        # Method 3: Anthropometric ratios
        ratio_bf = self._estimate_ratio_body_fat(anthro_data, user_sex)
        
        # Weighted combination with confidence assessment
        weights = [0.5, 0.3, 0.2]  # Navy formula gets highest weight
        bf_estimates = [navy_bf, visual_bf, ratio_bf]
        
        final_bf = sum(w * bf for w, bf in zip(weights, bf_estimates))
        
        # Determine confidence based on consistency
        max_deviation = max(abs(bf - final_bf) for bf in bf_estimates)
        if max_deviation < 3:
            confidence = "high"
        elif max_deviation < 6:
            confidence = "medium"
        else:
            confidence = "low"
        
        return round(final_bf, 1), confidence
    
    def _detect_posture_flags(self, landmarks: Any, image_shape: Tuple[int, int]) -> List[str]:
        """Detect postural deviations from pose landmarks"""
        flags = []
        height, width = image_shape[:2]
        
        try:
            # Get key points
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
            left_ear = landmarks[self.mp_pose.PoseLandmark.LEFT_EAR.value]
            right_ear = landmarks[self.mp_pose.PoseLandmark.RIGHT_EAR.value]
            
            # Check for rounded shoulders
            shoulder_y_avg = (left_shoulder.y + right_shoulder.y) / 2
            ear_y_avg = (left_ear.y + right_ear.y) / 2
            if shoulder_y_avg < ear_y_avg - 0.02:  # Shoulders higher than ears
                flags.append(PostureFlag.ROUNDED_SHOULDERS.value)
            
            # Check for asymmetric shoulders
            shoulder_y_diff = abs(left_shoulder.y - right_shoulder.y)
            if shoulder_y_diff > 0.03:  # Significant height difference
                flags.append(PostureFlag.ASYMMETRIC_SHOULDERS.value)
            
            # Check for forward head posture
            nose_x = nose.x
            shoulder_x_avg = (left_shoulder.x + right_shoulder.x) / 2
            if nose_x > shoulder_x_avg + 0.05:  # Head forward of shoulders
                flags.append(PostureFlag.FORWARD_HEAD.value)
            
            # Check for anterior pelvic tilt (simplified)
            hip_y_avg = (left_hip.y + right_hip.y) / 2
            if hip_y_avg < shoulder_y_avg - 0.4:  # Hip position relative to shoulders
                flags.append(PostureFlag.ANTERIOR_PELVIC_TILT.value)
                
        except Exception as e:
            logger.warning(f"Posture analysis failed: {e}")
        
        return flags
    
    def _stage6_output_json(self, pose_results: Any, anthro_data: Dict[str, float], 
                           bf_estimate: float, quality_score: float, 
                           confidence: str) -> Dict[str, Any]:
        """Stage 6: Create LLM-friendly JSON payload"""
        
        # Detect posture flags
        pose_alerts = []
        if pose_results and pose_results.pose_landmarks:
            pose_alerts = self._detect_posture_flags(
                pose_results.pose_landmarks.landmark, 
                (480, 640)  # Default shape for calculation
            )
        
        # Calculate additional metrics
        waist_to_hip_ratio = None
        if anthro_data.get('waist_cm') and anthro_data.get('hip_cm'):
            waist_to_hip_ratio = round(anthro_data['waist_cm'] / anthro_data['hip_cm'], 3)
        
        return {
            "poseAlerts": pose_alerts,
            "anthro": anthro_data,
            "bf_estimate": bf_estimate,
            "imageQuality": round(quality_score, 2),
            "confidence": confidence,
            "waist_to_hip_ratio": waist_to_hip_ratio,
            "analysis_timestamp": self._get_timestamp(),
            "version": "2.0"
        }
    
    # Helper methods
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _calculate_navy_body_fat(self, waist_cm: float, neck_cm: float, 
                                height_cm: float, sex: str, hip_cm: Optional[float] = None) -> float:
        """Calculate body fat using US Navy method"""
        try:
            if sex.lower() in ['male', 'm']:
                # Male formula
                bf = 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
            else:
                # Female formula (requires hip measurement)
                if not hip_cm:
                    hip_cm = waist_cm * 1.1  # Estimate if not available
                bf = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 78.387
            
            # Clamp to reasonable range
            return max(3.0, min(50.0, bf))
        except (ValueError, ZeroDivisionError):
            # Return default based on sex
            return 15.0 if sex.lower() in ['male', 'm'] else 23.0
    
    def _estimate_visual_body_fat(self, segmented_image: np.ndarray, sex: str) -> float:
        """Estimate body fat from visual analysis (simplified CNN simulation)"""
        # This is a simplified version - in production, you'd use a trained CNN
        gray = cv2.cvtColor(segmented_image, cv2.COLOR_BGR2GRAY)
        
        # Analyze body contour sharpness/definition
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        
        # More defined edges suggest lower body fat
        base_bf = 25.0 if sex.lower() in ['female', 'f'] else 18.0
        bf_adjustment = (0.5 - edge_density) * 20  # Rough estimate
        
        estimated_bf = base_bf + bf_adjustment
        return max(8.0, min(45.0, estimated_bf))
    
    def _estimate_ratio_body_fat(self, anthro_data: Dict[str, float], sex: str) -> float:
        """Estimate body fat using anthropometric ratios"""
        waist = anthro_data.get('waist_cm', 80)
        hip = anthro_data.get('hip_cm', 90)
        
        whr = waist / hip if hip > 0 else 0.8
        
        if sex.lower() in ['male', 'm']:
            # Male WHR body fat estimation
            if whr < 0.85:
                return 12.0
            elif whr < 0.95:
                return 18.0
            else:
                return 25.0
        else:
            # Female WHR body fat estimation  
            if whr < 0.75:
                return 16.0
            elif whr < 0.85:
                return 23.0
            else:
                return 32.0
    
    def _error_response(self, error_type: str, quality_score: float) -> Dict[str, Any]:
        """Return error response with minimal viable data"""
        return {
            "error": error_type,
            "poseAlerts": [],
            "anthro": {
                "shoulder_cm": 45.0,
                "waist_cm": 80.0,
                "hip_cm": 90.0,
                "chest_cm": 38.0,
                "neck_cm": 16.0,
                "thigh_cm": 36.0,
                "arm_cm": 14.0
            },
            "bf_estimate": 20.0,
            "imageQuality": quality_score,
            "confidence": "low",
            "waist_to_hip_ratio": 0.89,
            "analysis_timestamp": self._get_timestamp(),
            "version": "2.0"
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# Usage example and testing function
def test_vision_pipeline():
    """Test the vision pipeline with sample data"""
    pipeline = EnhancedVisionPipeline()
    
    # Test with sample parameters
    result = pipeline.process_image(
        image_path="sample_image.jpg",
        user_height_cm=175.0,
        user_weight_kg=75.0,
        user_sex="male"
    )
    
    print("Vision Pipeline Result:")
    print(json.dumps(result, indent=2))
    
    return result

if __name__ == "__main__":
    test_vision_pipeline()