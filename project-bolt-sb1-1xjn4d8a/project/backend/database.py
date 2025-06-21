from tinydb import TinyDB, Query
from typing import Dict, List, Any, Optional
import os

class Database:
    def __init__(self, db_path: str = "gym_coach.json"):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
        self.plans = self.db.table('plans')
    
    def create_user(self, user_data: Dict[str, Any]) -> None:
        """Create a new user"""
        self.users.insert(user_data)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        User = Query()
        result = self.users.search(User.email == email)
        return result[0] if result else None
    
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