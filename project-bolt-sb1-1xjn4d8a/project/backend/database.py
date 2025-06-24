from tinydb import TinyDB, Query
from typing import Dict, List, Any, Optional
import os
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path: str = "gym_coach.json"):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
        self.plans = self.db.table('plans')
        self.progress_entries = self.db.table('progress_entries')  # New
        self.workout_logs = self.db.table('workout_logs')          # New
        self.weight_logs = self.db.table('weight_logs')            # New
        self.body_measurements = self.db.table('body_measurements') # New
    
    def create_user(self, user_data: Dict[str, Any]) -> None:
        """Create a new user"""
        self.users.insert(user_data)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            User = Query()
            # First try the new structure
            result = self.users.search(User.email == email)
            if result:
                return result[0]
            
            # Fallback: check if we have the old structure where users are stored by email as key
            all_users = self.users.all()
            for user in all_users:
                if user.get('email') == email:
                    return user
            
            # Additional fallback: check if there's a different structure in the database
            # This handles the case where the JSON structure might be different
            try:
                with open(self.db._storage._handle.name, 'r') as f:
                    data = json.load(f)
                    if 'users' in data:
                        users_data = data['users']
                        # Handle dict-based storage
                        if isinstance(users_data, dict):
                            for user_data in users_data.values():
                                if isinstance(user_data, dict) and user_data.get('email') == email:
                                    return user_data
                        # Handle list-based storage
                        elif isinstance(users_data, list):
                            for user_data in users_data:
                                if isinstance(user_data, dict) and user_data.get('email') == email:
                                    return user_data
            except Exception as e:
                print(f"DEBUG: Error reading database directly: {e}")
            
            return None
        except Exception as e:
            print(f"DEBUG: Error in get_user_by_email: {e}")
            return None
    
    def store_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Store user's physical data"""
        self.user_data.insert(data)
    
    def get_latest_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest physical data"""
        UserData = Query()
        results = self.user_data.search(UserData.user_id == user_id)
        return max(results, key=lambda x: x['created_at']) if results else None
    
    def store_image_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        """Store image analysis results"""
        analysis['user_id'] = user_id
        self.image_analyses.insert(analysis)
    
    def get_latest_image_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest image analysis"""
        Analysis = Query()
        results = self.image_analyses.search(Analysis.user_id == user_id)
        return max(results, key=lambda x: x['created_at']) if results else None
    
    def store_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        """Store generated plan"""
        self.plans.insert(plan)
    
    def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user's plans"""
        Plan = Query()
        return self.plans.search(Plan.user_id == user_id)
    
    def get_latest_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's latest plan"""
        plans = self.get_user_plans(user_id)
        return max(plans, key=lambda x: x['created_at']) if plans else None
    
    # NEW: Progress tracking methods
    def store_progress_entry(self, user_id: str, progress_data: Dict[str, Any]) -> None:
        """Store daily progress entry"""
        progress_data["user_id"] = user_id
        progress_data["timestamp"] = datetime.utcnow().isoformat()
        self.progress_entries.insert(progress_data)
    
    def get_progress_entries(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get progress entries for the last N days"""
        Progress = Query()
        all_entries = self.progress_entries.search(Progress.user_id == user_id)
        
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
    
    def store_workout_log(self, user_id: str, workout_data: Dict[str, Any]) -> None:
        """Store completed workout log"""
        workout_data["user_id"] = user_id
        workout_data["timestamp"] = datetime.utcnow().isoformat()
        self.workout_logs.insert(workout_data)
    
    def get_workout_logs(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get workout logs for the last N days"""
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
    
    def store_weight_entry(self, user_id: str, weight_data: Dict[str, Any]) -> None:
        """Store weight measurement"""
        weight_data["user_id"] = user_id
        weight_data["timestamp"] = datetime.utcnow().isoformat()
        self.weight_logs.insert(weight_data)
    
    def get_weight_logs(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get weight logs for the last N days"""
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
    
    def store_body_measurements(self, user_id: str, measurement_data: Dict[str, Any]) -> None:
        """Store body measurements (waist, chest, arms, etc.)"""
        measurement_data["user_id"] = user_id
        measurement_data["timestamp"] = datetime.utcnow().isoformat()
        self.body_measurements.insert(measurement_data)
    
    def get_body_measurements(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get body measurements for the last N days"""
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
    
    def get_today_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get today's progress entry if exists"""
        today = datetime.utcnow().date()
        Progress = Query()
        progress_entries = self.progress_entries.search(Progress.user_id == user_id)
        
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