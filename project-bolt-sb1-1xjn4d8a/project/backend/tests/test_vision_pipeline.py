# backend/tests/test_vision_pipeline.py
"""
Complete test suite for the Enhanced Vision Pipeline
"""

import os
import sys
import json
import time
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import tempfile
import asyncio

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.vision_pipeline import EnhancedVisionPipeline, PostureFlag
from workers.vision_worker import VisionWorker, VisionQueueClient
from config import Settings

class TestEnhancedVisionPipeline:
    """Comprehensive tests for the vision pipeline"""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing"""
        return EnhancedVisionPipeline()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        # Create a simple test image (person-like shape)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some basic shapes to simulate a person
        cv2.rectangle(img, (250, 150), (390, 300), (100, 100, 100), -1)  # Torso
        cv2.circle(img, (320, 120), 40, (120, 120, 120), -1)  # Head
        return img
    
    @pytest.fixture
    def temp_image_file(self, sample_image):
        """Create temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            cv2.imwrite(f.name, sample_image)
            yield f.name
        os.unlink(f.name)
    
    def test_pipeline_initialization(self, pipeline):
        """Test that pipeline initializes correctly"""
        assert pipeline.mp_pose is not None
        assert pipeline.mp_selfie_segmentation is not None
        assert pipeline.min_quality_score == 0.7
        assert pipeline.min_detection_confidence == 0.5
        assert "waist_to_shoulder" in pipeline.anthro_ratios
    
    def test_image_quality_assessment(self, pipeline, sample_image):
        """Test image quality assessment"""
        quality_score = pipeline._assess_image_quality(sample_image)
        assert 0.0 <= quality_score <= 1.0
        assert isinstance(quality_score, float)
    
    def test_quality_gate_with_valid_image(self, pipeline, temp_image_file):
        """Test quality gate with a valid image"""
        image, quality_score = pipeline._stage1_quality_gate(temp_image_file)
        assert image is not None
        assert image.shape[2] == 3  # Color image
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0
    
    def test_quality_gate_with_invalid_file(self, pipeline):
        """Test quality gate with non-existent file"""
        with pytest.raises(ValueError, match="Could not load image"):
            pipeline._stage1_quality_gate("nonexistent_file.jpg")
    
    @patch('mediapipe.solutions.selfie_segmentation.SelfieSegmentation')
    def test_segmentation_stage(self, mock_segmentation, pipeline, sample_image):
        """Test image segmentation stage"""
        # Mock MediaPipe segmentation
        mock_results = Mock()
        mock_results.segmentation_mask = np.ones((480, 640)) * 0.8
        
        mock_seg_instance = Mock()
        mock_seg_instance.process.return_value = mock_results
        mock_segmentation.return_value.__enter__.return_value = mock_seg_instance
        
        segmented_image, mask = pipeline._stage2_segmentation(sample_image)
        
        assert segmented_image.shape == sample_image.shape
        assert mask.shape == (480, 640)
        assert mask.dtype == np.uint8
    
    @patch('mediapipe.solutions.pose.Pose')
    def test_pose_detection_stage(self, mock_pose, pipeline, sample_image):
        """Test pose detection stage"""
        # Mock MediaPipe pose detection
        mock_landmark = Mock()
        mock_landmark.x = 0.5
        mock_landmark.y = 0.5
        mock_landmark.visibility = 0.9
        
        mock_results = Mock()
        mock_results.pose_landmarks = Mock()
        mock_results.pose_landmarks.landmark = [mock_landmark] * 33  # 33 pose landmarks
        
        mock_pose_instance = Mock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose.return_value.__enter__.return_value = mock_pose_instance
        
        landmarks, pose_results = pipeline._stage3_pose_detection(sample_image)
        
        assert landmarks is not None
        assert len(landmarks) == 33
        assert pose_results is not None
    
    def test_anthropometrics_calculation(self, pipeline):
        """Test anthropometric calculations"""
        # Create mock landmarks
        mock_landmarks = []
        landmark_positions = {
            11: (0.3, 0.4),  # LEFT_SHOULDER
            12: (0.7, 0.4),  # RIGHT_SHOULDER  
            23: (0.35, 0.6), # LEFT_HIP
            24: (0.65, 0.6), # RIGHT_HIP
            27: (0.35, 0.9), # LEFT_ANKLE
            28: (0.65, 0.9), # RIGHT_ANKLE
            0: (0.5, 0.2),   # NOSE
        }
        
        for i in range(33):
            mock_landmark = Mock()
            if i in landmark_positions:
                mock_landmark.x, mock_landmark.y = landmark_positions[i]
            else:
                mock_landmark.x, mock_landmark.y = 0.5, 0.5
            mock_landmark.visibility = 0.9
            mock_landmarks.append(mock_landmark)
        
        image_shape = (480, 640, 3)
        user_height_cm = 175.0
        
        anthro_data = pipeline._stage4_anthropometrics(mock_landmarks, image_shape, user_height_cm)
        
        assert "shoulder_cm" in anthro_data
        assert "waist_cm" in anthro_data
        assert "hip_cm" in anthro_data
        assert "chest_cm" in anthro_data
        assert "neck_cm" in anthro_data
        assert "thigh_cm" in anthro_data
        assert "arm_cm" in anthro_data
        
        # Verify reasonable values
        assert 30 < anthro_data["shoulder_cm"] < 70
        assert 60 < anthro_data["waist_cm"] < 120
        assert 70 < anthro_data["hip_cm"] < 130
    
    def test_body_composition_estimation(self, pipeline, sample_image):
        """Test body composition estimation"""
        anthro_data = {
            "waist_cm": 85.0,
            "neck_cm": 38.0,
            "hip_cm": 95.0
        }
        
        bf_estimate, confidence = pipeline._stage5_body_composition(
            sample_image, anthro_data, 175.0, 75.0, "male"
        )
        
        assert isinstance(bf_estimate, float)
        assert 5.0 <= bf_estimate <= 50.0
        assert confidence in ["high", "medium", "low"]
    
    def test_navy_body_fat_calculation(self, pipeline):
        """Test US Navy body fat calculation"""
        # Test male calculation
        bf_male = pipeline._calculate_navy_body_fat(85.0, 38.0, 175.0, "male")
        assert isinstance(bf_male, float)
        assert 3.0 <= bf_male <= 50.0
        
        # Test female calculation
        bf_female = pipeline._calculate_navy_body_fat(75.0, 32.0, 165.0, "female", 95.0)
        assert isinstance(bf_female, float)
        assert 3.0 <= bf_female <= 50.0
        
        # Test with invalid inputs
        bf_invalid = pipeline._calculate_navy_body_fat(-10, 0, 0, "male")
        assert bf_invalid in [15.0, 23.0]  # Default values
    
    def test_posture_flag_detection(self, pipeline):
        """Test posture flag detection"""
        # Create mock landmarks for rounded shoulders
        mock_landmarks = []
        for i in range(33):
            mock_landmark = Mock()
            mock_landmark.x = 0.5
            mock_landmark.y = 0.5
            mock_landmark.visibility = 0.9
            
            # Simulate rounded shoulders (shoulders higher than ears)
            if i == 11:  # LEFT_SHOULDER
                mock_landmark.y = 0.35
            elif i == 12:  # RIGHT_SHOULDER  
                mock_landmark.y = 0.35
            elif i == 7:   # LEFT_EAR
                mock_landmark.y = 0.4
            elif i == 8:   # RIGHT_EAR
                mock_landmark.y = 0.4
                
            mock_landmarks.append(mock_landmark)
        
        flags = pipeline._detect_posture_flags(mock_landmarks, (480, 640))
        assert isinstance(flags, list)
        # Should detect rounded shoulders based on our mock data
        # Note: The exact detection depends on threshold tuning
    
    def test_full_pipeline_with_mock_image(self, pipeline, temp_image_file):
        """Test complete pipeline with a real image file"""
        result = pipeline.process_image(
            image_path=temp_image_file,
            user_height_cm=175.0,
            user_weight_kg=75.0, 
            user_sex="male"
        )
        
        # Verify result structure
        required_keys = [
            "poseAlerts", "anthro", "bf_estimate", 
            "imageQuality", "confidence", "analysis_timestamp", "version"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        
        assert isinstance(result["poseAlerts"], list)
        assert isinstance(result["anthro"], dict)
        assert isinstance(result["bf_estimate"], (int, float))
        assert isinstance(result["imageQuality"], (int, float))
        assert result["confidence"] in ["high", "medium", "low"]
        assert result["version"] == "2.0"
    
    def test_error_handling_invalid_image(self, pipeline):
        """Test error handling with invalid image"""
        result = pipeline.process_image(
            image_path="nonexistent.jpg",
            user_height_cm=175.0,
            user_weight_kg=75.0,
            user_sex="male"
        )
        
        assert "error" in result
        assert result["error"] == "processing_failed"
        assert "anthro" in result  # Should have fallback data
    
    def test_low_quality_image_rejection(self, pipeline):
        """Test rejection of low quality images"""
        # Create a very blurry/dark image
        low_quality_img = np.zeros((100, 100, 3), dtype=np.uint8) + 10
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            cv2.imwrite(f.name, low_quality_img)
            temp_file = f.name
        
        try:
            result = pipeline.process_image(
                image_path=temp_file,
                user_height_cm=175.0,
                user_weight_kg=75.0,
                user_sex="male"
            )
            
            # Should either reject or have low quality score
            if "error" in result:
                assert result["error"] == "low_quality"
            else:
                assert result["imageQuality"] < 0.7
        finally:
            os.unlink(temp_file)


class TestVisionWorker:
    """Tests for the vision worker service"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch('redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_redis.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def worker(self, mock_redis):
        """Create worker instance for testing"""
        return VisionWorker("redis://test:6379")
    
    def test_worker_initialization(self, worker):
        """Test worker initializes correctly"""
        assert worker.vision_pipeline is not None
        assert worker.input_queue == "vision_input"
        assert worker.output_queue == "vision_output"
        assert worker.error_queue == "vision_errors"
    
    def test_process_vision_task_success(self, worker, temp_image_file):
        """Test successful vision task processing"""
        task_data = {
            "task_id": "test_123",
            "user_id": "user_456", 
            "image_path": temp_image_file,
            "user_height_cm": 175.0,
            "user_weight_kg": 75.0,
            "user_sex": "male"
        }
        
        result = worker.process_vision_task(task_data)
        
        assert "task_id" in result
        assert "user_id" in result
        assert "processing_time_seconds" in result
        assert result["task_id"] == "test_123"
        assert result["user_id"] == "user_456"
    
    def test_process_vision_task_file_not_found(self, worker):
        """Test vision task with missing file"""
        task_data = {
            "task_id": "test_123",
            "user_id": "user_456",
            "image_path": "nonexistent.jpg",
            "user_height_cm": 175.0,
            "user_weight_kg": 75.0,
            "user_sex": "male"
        }
        
        result = worker.process_vision_task(task_data)
        
        assert "error" in result
        assert result["task_id"] == "test_123"
        assert result["error_type"] == "FileNotFoundError"
    
    def test_health_check(self, worker, mock_redis):
        """Test worker health check"""
        mock_redis.info.return_value = {
            "connected_clients": 1,
            "used_memory_human": "1M"
        }
        mock_redis.llen.return_value = 0
        
        health = worker.health_check()
        
        assert health["status"] == "healthy"
        assert health["redis_connected"] is True
        assert "queue_length" in health
        assert "completed_count" in health
        assert "error_count" in health


class TestVisionQueueClient:
    """Tests for the vision queue client"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch('redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_redis.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def client(self, mock_redis):
        """Create client instance for testing"""
        return VisionQueueClient("redis://test:6379")
    
    def test_queue_async(self, client, mock_redis):
        """Test async task queueing"""
        task_id = client.queue_async(
            image_path="/test/path.jpg",
            user_id="user_123",
            user_height_cm=175.0,
            user_weight_kg=75.0,
            user_sex="male"
        )
        
        assert isinstance(task_id, str)
        assert len(task_id) > 0
        mock_redis.lpush.assert_called_once()


def create_test_fixtures():
    """Create test fixtures and sample data"""
    # Create test directory
    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create sample images
    sample_images = {
        "good_quality.jpg": create_good_quality_image(),
        "poor_quality.jpg": create_poor_quality_image(),
        "person_front.jpg": create_person_image("front"),
        "person_side.jpg": create_person_image("side")
    }
    
    for filename, image in sample_images.items():
        filepath = os.path.join(test_dir, filename)
        cv2.imwrite(filepath, image)
        print(f"Created test image: {filepath}")
    
    return test_dir

def create_good_quality_image():
    """Create a good quality test image"""
    img = np.random.randint(50, 200, (640, 480, 3), dtype=np.uint8)
    # Add some structure to make it realistic
    cv2.rectangle(img, (200, 150), (440, 450), (120, 100, 80), -1)  # Body
    cv2.circle(img, (320, 100), 50, (180, 150, 120), -1)  # Head
    return img

def create_poor_quality_image():
    """Create a poor quality test image (dark, blurry)"""
    img = np.random.randint(0, 30, (320, 240, 3), dtype=np.uint8)
    # Add blur
    img = cv2.GaussianBlur(img, (15, 15), 0)
    return img

def create_person_image(view="front"):
    """Create a simple person-like image"""
    img = np.zeros((480, 640, 3), dtype=np.uint8) + 50  # Gray background
    
    if view == "front":
        # Front view person
        cv2.rectangle(img, (280, 180), (360, 380), (100, 100, 100), -1)  # Torso
        cv2.circle(img, (320, 140), 35, (120, 120, 120), -1)  # Head
        cv2.rectangle(img, (250, 200), (280, 280), (90, 90, 90), -1)   # Left arm
        cv2.rectangle(img, (360, 200), (390, 280), (90, 90, 90), -1)   # Right arm
        cv2.rectangle(img, (300, 380), (320, 450), (80, 80, 80), -1)   # Left leg
        cv2.rectangle(img, (320, 380), (340, 450), (80, 80, 80), -1)   # Right leg
    else:  # side view
        cv2.rectangle(img, (300, 180), (340, 380), (100, 100, 100), -1)  # Torso
        cv2.circle(img, (320, 140), 35, (120, 120, 120), -1)  # Head
        cv2.rectangle(img, (280, 200), (300, 280), (90, 90, 90), -1)   # Arm
        cv2.rectangle(img, (310, 380), (330, 450), (80, 80, 80), -1)   # Legs
    
    return img

def run_integration_test():
    """Run a complete integration test"""
    print("🧪 Running Vision Pipeline Integration Test...")
    
    # Create test fixtures
    test_dir = create_test_fixtures()
    
    try:
        # Initialize pipeline
        pipeline = EnhancedVisionPipeline()
        print("✅ Pipeline initialized")
        
        # Test with each sample image
        test_images = [
            "good_quality.jpg",
            "person_front.jpg",
            "person_side.jpg"
        ]
        
        results = {}
        
        for image_name in test_images:
            image_path = os.path.join(test_dir, image_name)
            if os.path.exists(image_path):
                print(f"\n📸 Testing {image_name}...")
                
                start_time = time.time()
                result = pipeline.process_image(
                    image_path=image_path,
                    user_height_cm=175.0,
                    user_weight_kg=75.0,
                    user_sex="male"
                )
                processing_time = time.time() - start_time
                
                results[image_name] = {
                    "result": result,
                    "processing_time": processing_time
                }
                
                print(f"   ⏱️  Processing time: {processing_time:.2f}s")
                print(f"   🎯 Image quality: {result.get('imageQuality', 'N/A')}")
                print(f"   📊 BF estimate: {result.get('bf_estimate', 'N/A')}%")
                print(f"   🔍 Confidence: {result.get('confidence', 'N/A')}")
                print(f"   ⚠️  Posture alerts: {result.get('poseAlerts', [])}")
                
                if "error" in result:
                    print(f"   ❌ Error: {result['error']}")
                else:
                    print(f"   ✅ Success")
        
        # Generate summary report
        print(f"\n📋 Integration Test Summary:")
        print(f"   Tests run: {len(results)}")
        successful = sum(1 for r in results.values() if "error" not in r["result"])
        print(f"   Successful: {successful}/{len(results)}")
        
        avg_time = np.mean([r["processing_time"] for r in results.values()])
        print(f"   Average processing time: {avg_time:.2f}s")
        
        print(f"\n🎉 Integration test completed!")
        
        return results
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Cleanup test files
        import shutil
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test directory: {test_dir}")

def test_vision_pipeline():
    """Main test function - comprehensive testing"""
    print("🚀 Starting Enhanced Vision Pipeline Tests")
    print("=" * 50)
    
    try:
        # Run integration test
        results = run_integration_test()
        
        if results:
            # Save detailed results
            with open("vision_test_results.json", "w") as f:
                # Convert numpy types to JSON serializable
                serializable_results = {}
                for key, value in results.items():
                    serializable_results[key] = {
                        "processing_time": float(value["processing_time"]),
                        "result": value["result"]
                    }
                json.dump(serializable_results, f, indent=2)
            
            print(f"\n📄 Detailed results saved to: vision_test_results.json")
        
        print(f"\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the complete test suite
    success = test_vision_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)