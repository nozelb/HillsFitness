from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Gym AI Coach API"
    version: str = "2.0.0"
    debug: bool = True
    
    # Database settings
    database_path: str = "gym_coach_enhanced.json"
    
    # Security settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File upload settings
    upload_dir: str = "uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: list = ["image/jpeg", "image/png", "image/jpg"]
    
    # API settings
    api_prefix: str = "/api"
    
    # CORS settings
    allowed_origins: list = ["*"]  # In production, specify exact origins
    
    # MediaPipe settings
    mp_model_complexity: int = 2
    mp_min_detection_confidence: float = 0.5
    
    # Plan generation settings
    min_exercises_per_workout: int = 5
    max_exercises_per_workout: int = 8
    plan_duration_weeks: int = 4
    
    # Safety limits
    min_calories_male: int = 1500
    min_calories_female: int = 1200
    max_calorie_deficit: float = 0.25
    min_protein_per_kg: float = 0.8
    
    # Redis settings (for future caching)
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()