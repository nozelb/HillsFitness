# backend/config.py - Enhanced Configuration
from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Gym AI Coach API Enhanced"
    version: str = "2.1.0"
    debug: bool = True
    
    # Database settings
    database_path: str = "data/gym_coach_enhanced.json"
    
    # Security settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File upload settings
    upload_dir: str = "uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/jpg"]
    
    # API settings
    api_prefix: str = "/api"
    
    # CORS settings
    allowed_origins: List[str] = ["*"]  # In production, specify exact origins
    
    # Vision Pipeline settings
    mp_model_complexity: int = 2
    mp_min_detection_confidence: float = 0.5
    mp_min_tracking_confidence: float = 0.5
    
    # Image quality thresholds
    min_image_quality_score: float = 0.7
    blur_threshold: float = 500.0
    brightness_tolerance: float = 0.3
    
    # Body composition estimation settings
    navy_formula_enabled: bool = True
    visual_analysis_enabled: bool = True
    anthropometric_ratios: dict = {
        "waist_to_shoulder": 0.75,
        "hip_to_shoulder": 0.95,
        "neck_to_shoulder": 0.35
    }
    
    # Plan generation settings
    min_exercises_per_workout: int = 5
    max_exercises_per_workout: int = 8
    plan_duration_weeks: int = 4
    
    # Safety limits for nutrition
    min_calories_male: int = 1500
    min_calories_female: int = 1200
    max_calorie_deficit: float = 0.25
    min_protein_per_kg: float = 0.8
    max_protein_per_kg: float = 3.0
    
    # Redis settings for vision worker
    redis_url: Optional[str] = "redis://localhost:6379"
    redis_vision_input_queue: str = "vision_input"
    redis_vision_output_queue: str = "vision_output"
    redis_vision_error_queue: str = "vision_errors"
    
    # Vision worker settings
    vision_worker_enabled: bool = True
    vision_processing_timeout: int = 60  # seconds
    vision_worker_concurrency: int = 2
    max_concurrent_vision_tasks: int = 10
    
    # Posture detection thresholds
    posture_detection_enabled: bool = True
    shoulder_asymmetry_threshold: float = 0.03
    forward_head_threshold: float = 0.05
    rounded_shoulder_threshold: float = 0.02
    
    # Background task settings
    cleanup_uploaded_files: bool = True
    file_cleanup_delay_hours: int = 1
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_request_logging: bool = True
    
    # Performance settings
    enable_image_caching: bool = False  # Set to True with Redis in production
    cache_ttl_seconds: int = 3600
    
    # Machine Learning model settings (for future CNN integration)
    ml_model_path: Optional[str] = None
    use_gpu_acceleration: bool = False
    model_confidence_threshold: float = 0.8
    
    # Health check settings
    health_check_enabled: bool = True
    health_check_interval: int = 30
    
    # Privacy and compliance
    gdpr_compliance_mode: bool = True
    data_retention_days: int = 30
    anonymize_stored_data: bool = False
    
    # Feature flags
    enable_advanced_anthropometrics: bool = True
    enable_posture_correction_recommendations: bool = True
    enable_real_time_feedback: bool = False
    enable_progress_tracking: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

# Create settings instance
settings = Settings()

# Validation function
def validate_settings():
    """Validate critical settings on startup"""
    errors = []
    
    # Check upload directory
    if not os.path.exists(settings.upload_dir):
        try:
            os.makedirs(settings.upload_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create upload directory: {e}")
    
    # Check database directory
    db_dir = os.path.dirname(settings.database_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create database directory: {e}")
    
    # Validate security settings
    if settings.secret_key == "your-secret-key-here-change-in-production":
        errors.append("Secret key must be changed in production")
    
    # Validate thresholds
    if settings.min_image_quality_score > 1.0 or settings.min_image_quality_score < 0.0:
        errors.append("Image quality score must be between 0.0 and 1.0")
    
    if settings.max_calorie_deficit > 0.5:
        errors.append("Maximum calorie deficit should not exceed 50%")
    
    # Check Redis connection if worker enabled
    if settings.vision_worker_enabled and settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
        except Exception as e:
            errors.append(f"Redis connection failed: {e}")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

# Environment-specific configurations
class DevelopmentSettings(Settings):
    debug: bool = True
    log_level: str = "DEBUG"
    enable_request_logging: bool = True
    file_cleanup_delay_hours: int = 0.1  # 6 minutes for faster testing

class ProductionSettings(Settings):
    debug: bool = False
    log_level: str = "INFO"
    allowed_origins: List[str] = ["https://yourdomain.com"]
    gdpr_compliance_mode: bool = True
    cleanup_uploaded_files: bool = True
    enable_image_caching: bool = True
    use_gpu_acceleration: bool = True

class TestSettings(Settings):
    debug: bool = True
    database_path: str = "test_gym_coach.json"
    upload_dir: str = "test_uploads"
    redis_url: Optional[str] = None  # Disable Redis for tests
    vision_worker_enabled: bool = False
    cleanup_uploaded_files: bool = False
    log_level: str = "WARNING"

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()

# Initialize settings with validation
try:
    settings = get_settings()
    validate_settings()
except Exception as e:
    print(f"Configuration error: {e}")
    # Fall back to default settings
    settings = Settings()

# Export commonly used settings
UPLOAD_DIR = settings.upload_dir
MAX_UPLOAD_SIZE = settings.max_upload_size
SECRET_KEY = settings.secret_key
REDIS_URL = settings.redis_url
DATABASE_PATH = settings.database_path