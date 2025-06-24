from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from typing import Dict, List, Any, Optional
import os
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path: str = "gym_coach.json"):
        self.db_path = db_path
        
        # Initialize database with proper error handling
        try:
            # Check if file exists and is valid JSON
            if os.path.exists(db_path):
                try:
                    with open(db_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            json.loads(content)  # Validate JSON
                        else:
                            # File is empty, initialize with empty structure
                            self._create_empty_db()
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"DEBUG: Database file corrupted, reinitializing: {e}")
                    self._create_empty_db()
            else:
                # File doesn't exist, create it
                self._create_empty_db()
            
            # Now initialize TinyDB
            self.db = TinyDB(db_path, storage=CachingMiddleware(JSONStorage))
            self.users = self.db.table('users')
            self.user_data = self.db.table('user_data')
            self.image_analyses = self.db.table('image_analyses')
            self.plans = self.db.table('plans')
            self.progress_entries = self.db.table('progress_entries')
            self.workout_logs = self.db.table('workout_logs')
            self.weight_logs = self.db.table('weight_logs')
            self.body_measurements = self.db.table('body_measurements')
            
            print(f"DEBUG: Database initialized successfully. Users count: {len(self.users.all())}")
            
        except Exception as e:
            print(f"DEBUG: Critical database initialization error: {e}")
            # Force create empty database
            self._create_empty_db()
            self.db = TinyDB(db_path, storage=CachingMiddleware(JSONStorage))
            self.users = self.db.table('users')
            self.user_data = self.db.table('user_data')
            self.image_analyses = self.db.table('image_analyses')
            self.plans = self.db.table('plans')
            self.progress_entries = self.db.table('progress_entries')
            self.workout_logs = self.db.table('workout_logs')
            self.weight_logs = self.db.table('weight_logs')
            self.body_measurements = self.db.table('body_measurements')
    
    def _create_empty_db(self):
        """Create an empty database file with proper structure"""
        empty_structure = {
            "_default": {},
            "users": {},
            "user_data": {},
            "image_analyses": {},
            "plans": {},
            "progress_entries": {},
            "workout_logs": {},
            "weight_logs": {},
            "body_measurements": {}
        }
        
        try:
            with open(self.db_path, 'w') as f:
                json.dump(empty_structure, f, indent=2)
            print("DEBUG: Created empty database file")
        except Exception as e:
            print(f"DEBUG: Error creating empty database: {e}")
    
    def create_user(self, user_data: Dict[str, Any]) -> None:
        """Create a new user"""
        try:
            print(f"DEBUG: Creating user: {user_data['email']}")
            self.users.insert(user_data)
            print(f"DEBUG: User created successfully. Total users: {len(self.users.all())}")
        except Exception as e:
            print(f"DEBUG: Error creating user: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            print(f"DEBUG: Looking for user with email: {email}")
            User = Query()
            result = self.users.search(User.email == email)
            print(f"DEBUG: Search result: {result}")
            return result[0] if result else None
        except Exception as e:
            print(f"DEBUG: Error in get_user_by_email: {e}")
            return None
    
    def store_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Store user's physical data"""
        try:
            self.user_data.insert(data)
        except Exception as e:
            print(f"DEBUG: Error storing user data: {e}")
            raise
    
    def get_latest_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest physical data"""
        try:
            UserData = Query()
            results = self.user_data.search(UserData.user_id == user_id)
            return max(results, key=lambda x: x['created_at']) if results else None
        except Exception as e:
            print(f"DEBUG: Error getting user data: {e}")
            return None
    
    def store_image_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        """Store image analysis results"""
        try:
            analysis['user_id'] = user_id
            self.image_analyses.insert(analysis)
        except Exception as e:
            print(f"DEBUG: Error storing image analysis: {e}")
            raise
    
    def get_latest_image_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest image analysis"""
        try:
            Analysis = Query()
            results = self.image_analyses.search(Analysis.user_id == user_id)
            return max(results, key=lambda x: x['created_at']) if results else None
        except Exception as e:
            print(f"DEBUG: Error getting image analysis: {e}")
            return None
    
    def store_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        """Store generated plan"""
        try:
            self.plans.insert(plan)
        except Exception as e:
            print(f"DEBUG: Error storing plan: {e}")
            raise
    
    def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user's plans"""
        try:
            Plan = Query()
            return self.plans.search(Plan.user_id == user_id)
        except Exception as e:
            print(f"DEBUG: Error getting user plans: {e}")
            return []
    
    def get_latest_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest plan"""
        try:
            plans = self.get_user_plans(user_id)
            return max(plans, key=lambda x: x['created_at']) if plans else None
        except Exception as e:
            print(f"DEBUG: Error getting latest plan: {e}")
            return None
    
    # Progress tracking methods
    def store_progress_entry(self, user_id: str, progress_data: Dict[str, Any]) -> None:
        """Store daily progress entry"""
        try:
            progress_data["user_id"] = user_id
            progress_data["timestamp"] = datetime.utcnow().isoformat()
            self.progress_entries.insert(progress_data)
        except Exception as e:
            print(f"DEBUG: Error storing progress entry: {e}")
            raise
    
    def get_progress_entries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get progress entries for the last N days"""
        try:
            Progress = Query()
            all_entries = self.progress_entries.search(Progress.user_id == user_id)
            
            if not all_entries:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_entries = []
            
            for entry in all_entries:
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date >= cutoff_date:
                    recent_entries.append(entry)
            
            return sorted(recent_entries, key=lambda x: x["timestamp"])
        except Exception as e:
            print(f"DEBUG: Error getting progress entries: {e}")
            return []
    
    def store_workout_log(self, user_id: str, workout_data: Dict[str, Any]) -> None:
        """Store completed workout log"""
        try:
            workout_data["user_id"] = user_id
            workout_data["timestamp"] = datetime.utcnow().isoformat()
            self.workout_logs.insert(workout_data)
        except Exception as e:
            print(f"DEBUG: Error storing workout log: {e}")
            raise
    
    def get_workout_logs(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get workout logs for the last N days"""
        try:
            WorkoutLog = Query()
            all_logs = self.workout_logs.search(WorkoutLog.user_id == user_id)
            
            if not all_logs:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_logs = []
            
            for log in all_logs:
                log_date = datetime.fromisoformat(log["timestamp"])
                if log_date >= cutoff_date:
                    recent_logs.append(log)
            
            return sorted(recent_logs, key=lambda x: x["timestamp"])
        except Exception as e:
            print(f"DEBUG: Error getting workout logs: {e}")
            return []
    
    def store_weight_entry(self, user_id: str, weight_data: Dict[str, Any]) -> None:
        """Store weight measurement"""
        try:
            weight_data["user_id"] = user_id
            weight_data["timestamp"] = datetime.utcnow().isoformat()
            self.weight_logs.insert(weight_data)
        except Exception as e:
            print(f"DEBUG: Error storing weight entry: {e}")
            raise
    
    def get_weight_logs(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get weight logs for the last N days"""
        try:
            WeightLog = Query()
            all_logs = self.weight_logs.search(WeightLog.user_id == user_id)
            
            if not all_logs:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_logs = []
            
            for log in all_logs:
                log_date = datetime.fromisoformat(log["timestamp"])
                if log_date >= cutoff_date:
                    recent_logs.append(log)
            
            return sorted(recent_logs, key=lambda x: x["timestamp"])
        except Exception as e:
            print(f"DEBUG: Error getting weight logs: {e}")
            return []
    
    def store_body_measurements(self, user_id: str, measurement_data: Dict[str, Any]) -> None:
        """Store body measurements"""
        try:
            measurement_data["user_id"] = user_id
            measurement_data["timestamp"] = datetime.utcnow().isoformat()
            self.body_measurements.insert(measurement_data)
        except Exception as e:
            print(f"DEBUG: Error storing body measurements: {e}")
            raise
    
    def get_body_measurements(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get body measurements for the last N days"""
        try:
            Measurements = Query()
            all_measurements = self.body_measurements.search(Measurements.user_id == user_id)
            
            if not all_measurements:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_measurements = []
            
            for measurement in all_measurements:
                measurement_date = datetime.fromisoformat(measurement["timestamp"])
                if measurement_date >= cutoff_date:
                    recent_measurements.append(measurement)
            
            return sorted(recent_measurements, key=lambda x: x["timestamp"])
        except Exception as e:
            print(f"DEBUG: Error getting body measurements: {e}")
            return []
    
    def get_today_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get today's progress entry if exists"""
        try:
            today = datetime.utcnow().date()
            Progress = Query()
            progress_entries = self.progress_entries.search(Progress.user_id == user_id)
            
            for entry in reversed(progress_entries):
                entry_date = datetime.fromisoformat(entry["timestamp"]).date()
                if entry_date == today:
                    return entry
            
            return None
        except Exception as e:
            print(f"DEBUG: Error getting today's progress: {e}")
            return None
    
    def get_weekly_workout_stats(self, user_id: str) -> Dict[str, Any]:
        """Get workout statistics for the current week"""
        try:
            week_start = datetime.utcnow() - timedelta(days=7)
            workout_logs = self.get_workout_logs(user_id, days=7)
            
            completed_workouts = len(workout_logs)
            total_duration = sum(log.get("duration_minutes", 0) for log in workout_logs)
            
            return {
                "completed_workouts": completed_workouts,
                "total_duration_minutes": total_duration,
                "week_start": week_start.isoformat()
            }
        except Exception as e:
            print(f"DEBUG: Error getting weekly workout stats: {e}")
            return {
                "completed_workouts": 0,
                "total_duration_minutes": 0,
                "week_start": datetime.utcnow().isoformat()
            }