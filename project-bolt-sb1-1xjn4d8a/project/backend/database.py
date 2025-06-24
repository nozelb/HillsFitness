import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class Database:
    """Simple JSON-based database for development"""
    
    def __init__(self, db_file: str = "data/database.json"):
        self.db_file = db_file
        self.db_dir = os.path.dirname(db_file)
        
        # Create data directory if it doesn't exist
        if self.db_dir and not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        # Initialize database structure
        self.db_structure = {
            "users": {},
            "user_data": {},
            "image_analyses": {},
            "plans": {},
            "progress_entries": {},  # New: Daily progress tracking
            "workout_logs": {},      # New: Workout completion logs
            "weight_logs": {},       # New: Weight tracking over time
            "body_measurements": {}  # New: Body measurement tracking
        }
        
        self._load_db()
    
    def _load_db(self):
        """Load database from file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.data = json.loads(content)
                        # Ensure all required collections exist
                        for key, default in self.db_structure.items():
                            if key not in self.data:
                                self.data[key] = default
                    else:
                        self.data = self.db_structure.copy()
            else:
                self.data = self.db_structure.copy()
        except (json.JSONDecodeError, FileNotFoundError):
            self.data = self.db_structure.copy()
    
    def _save_db(self):
        """Save database to file"""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    # User management
    def create_user(self, user_data: Dict[str, Any]):
        """Create a new user"""
        self.data["users"][user_data["email"]] = user_data
        self._save_db()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return self.data["users"].get(email)
    
    # User data storage
    def store_user_data(self, user_id: str, user_data: Dict[str, Any]):
        """Store user's physical data"""
        if user_id not in self.data["user_data"]:
            self.data["user_data"][user_id] = []
        self.data["user_data"][user_id].append(user_data)
        self._save_db()
    
    def get_latest_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest physical data"""
        user_data_list = self.data["user_data"].get(user_id, [])
        return user_data_list[-1] if user_data_list else None
    
    def get_user_data_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user data entries for tracking progress"""
        return self.data["user_data"].get(user_id, [])
    
    # Image analysis
    def store_image_analysis(self, user_id: str, analysis_data: Dict[str, Any]):
        """Store image analysis results"""
        if user_id not in self.data["image_analyses"]:
            self.data["image_analyses"][user_id] = []
        self.data["image_analyses"][user_id].append(analysis_data)
        self._save_db()
    
    def get_latest_image_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest image analysis"""
        analyses = self.data["image_analyses"].get(user_id, [])
        return analyses[-1] if analyses else None
    
    # Plans
    def store_plan(self, user_id: str, plan_data: Dict[str, Any]):
        """Store generated plan"""
        if user_id not in self.data["plans"]:
            self.data["plans"][user_id] = []
        self.data["plans"][user_id].append(plan_data)
        self._save_db()
    
    def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's plans"""
        return self.data["plans"].get(user_id, [])
    
    def get_latest_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest plan"""
        plans = self.data["plans"].get(user_id, [])
        return plans[-1] if plans else None
    
    # NEW: Progress tracking methods
    def store_progress_entry(self, user_id: str, progress_data: Dict[str, Any]):
        """Store daily progress entry"""
        if user_id not in self.data["progress_entries"]:
            self.data["progress_entries"][user_id] = []
        progress_data["timestamp"] = datetime.utcnow().isoformat()
        self.data["progress_entries"][user_id].append(progress_data)
        self._save_db()
    
    def get_progress_entries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get progress entries for the last N days"""
        all_entries = self.data["progress_entries"].get(user_id, [])
        if not all_entries:
            return []
        
        # Filter entries from the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_entries = []
        
        for entry in all_entries:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if entry_date >= cutoff_date:
                recent_entries.append(entry)
        
        return sorted(recent_entries, key=lambda x: x["timestamp"])
    
    def store_workout_log(self, user_id: str, workout_data: Dict[str, Any]):
        """Store completed workout log"""
        if user_id not in self.data["workout_logs"]:
            self.data["workout_logs"][user_id] = []
        workout_data["timestamp"] = datetime.utcnow().isoformat()
        self.data["workout_logs"][user_id].append(workout_data)
        self._save_db()
    
    def get_workout_logs(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get workout logs for the last N days"""
        all_logs = self.data["workout_logs"].get(user_id, [])
        if not all_logs:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_logs = []
        
        for log in all_logs:
            log_date = datetime.fromisoformat(log["timestamp"])
            if log_date >= cutoff_date:
                recent_logs.append(log)
        
        return sorted(recent_logs, key=lambda x: x["timestamp"])
    
    def store_weight_entry(self, user_id: str, weight_data: Dict[str, Any]):
        """Store weight measurement"""
        if user_id not in self.data["weight_logs"]:
            self.data["weight_logs"][user_id] = []
        weight_data["timestamp"] = datetime.utcnow().isoformat()
        self.data["weight_logs"][user_id].append(weight_data)
        self._save_db()
    
    def get_weight_logs(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get weight logs for the last N days"""
        all_logs = self.data["weight_logs"].get(user_id, [])
        if not all_logs:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_logs = []
        
        for log in all_logs:
            log_date = datetime.fromisoformat(log["timestamp"])
            if log_date >= cutoff_date:
                recent_logs.append(log)
        
        return sorted(recent_logs, key=lambda x: x["timestamp"])
    
    def store_body_measurements(self, user_id: str, measurement_data: Dict[str, Any]):
        """Store body measurements (waist, chest, arms, etc.)"""
        if user_id not in self.data["body_measurements"]:
            self.data["body_measurements"][user_id] = []
        measurement_data["timestamp"] = datetime.utcnow().isoformat()
        self.data["body_measurements"][user_id].append(measurement_data)
        self._save_db()
    
    def get_body_measurements(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get body measurements for the last N days"""
        all_measurements = self.data["body_measurements"].get(user_id, [])
        if not all_measurements:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_measurements = []
        
        for measurement in all_measurements:
            measurement_date = datetime.fromisoformat(measurement["timestamp"])
            if measurement_date >= cutoff_date:
                recent_measurements.append(measurement)
        
        return sorted(recent_measurements, key=lambda x: x["timestamp"])
    
    def get_today_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get today's progress entry if exists"""
        today = datetime.utcnow().date()
        progress_entries = self.data["progress_entries"].get(user_id, [])
        
        for entry in reversed(progress_entries):  # Check most recent first
            entry_date = datetime.fromisoformat(entry["timestamp"]).date()
            if entry_date == today:
                return entry
        
        return None
    
    def get_weekly_workout_stats(self, user_id: str) -> Dict[str, Any]:
        """Get workout statistics for the current week"""
        week_start = datetime.utcnow() - timedelta(days=7)
        workout_logs = self.get_workout_logs(user_id, days=7)
        
        completed_workouts = len(workout_logs)
        total_duration = sum(log.get("duration_minutes", 0) for log in workout_logs)
        
        return {
            "completed_workouts": completed_workouts,
            "total_duration_minutes": total_duration,
            "week_start": week_start.isoformat()
        }