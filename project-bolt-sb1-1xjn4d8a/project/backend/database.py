# database_v2.py - Enhanced database with new tables

from tinydb import TinyDB, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import json

class EnhancedDatabase(Database):
    def __init__(self, db_path: str = "gym_coach.json"):
        super().__init__(db_path)
        
        # New tables
        self.user_profiles = self.db.table('user_profiles')
        self.accepted_plans = self.db.table('accepted_plans')
        self.workout_sessions = self.db.table('workout_sessions')
        self.progress_photos = self.db.table('progress_photos')
        self.height_history = self.db.table('height_history')
        self.plan_regenerations = self.db.table('plan_regenerations')
    
    # User Profile Management
    def create_or_update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Create or update user profile with static data"""
        Profile = Query()
        existing = self.user_profiles.search(Profile.user_id == user_id)
        
        profile_data['user_id'] = user_id
        profile_data['updated_at'] = datetime.utcnow().isoformat()
        
        if existing:
            self.user_profiles.update(profile_data, Profile.user_id == user_id)
        else:
            profile_data['created_at'] = datetime.utcnow().isoformat()
            self.user_profiles.insert(profile_data)
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with calculated age"""
        Profile = Query()
        result = self.user_profiles.search(Profile.user_id == user_id)
        
        if result:
            profile = result[0]
            # Calculate age
            dob = datetime.fromisoformat(profile['date_of_birth']).date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            profile['calculated_age'] = age
            return profile
        return None
    
    # Height tracking for growing users
    def store_height_entry(self, user_id: str, height: float) -> None:
        """Track height changes over time"""
        self.height_history.insert({
            'user_id': user_id,
            'height_cm': height,
            'recorded_at': datetime.utcnow().isoformat()
        })
    
    def get_latest_height(self, user_id: str) -> Optional[float]:
        """Get most recent height measurement"""
        Height = Query()
        entries = self.height_history.search(Height.user_id == user_id)
        if entries:
            latest = max(entries, key=lambda x: x['recorded_at'])
            return latest['height_cm']
        return None
    
    # Plan acceptance and tracking
    def accept_plan(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Mark plan as accepted and set up 4-week schedule"""
        start_date = date.today()
        end_date = start_date + timedelta(weeks=4)
        
        acceptance_record = {
            'plan_id': plan_id,
            'user_id': user_id,
            'accepted_at': datetime.utcnow().isoformat(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'status': 'active'
        }
        
        self.accepted_plans.insert(acceptance_record)
        
        # Update plan status
        Plan = Query()
        self.plans.update(
            {'status': 'accepted', 'start_date': start_date.isoformat()},
            Plan.id == plan_id
        )
        
        # Generate workout schedule
        self._generate_workout_schedule(user_id, plan_id, start_date)
        
        return acceptance_record
    
    def _generate_workout_schedule(self, user_id: str, plan_id: str, start_date: date) -> None:
        """Create workout session schedule for 4 weeks"""
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            return
        
        training_days = plan.get('training_days_per_week', 4)
        current_date = start_date
        
        for week_num in range(1, 5):
            workouts_scheduled = 0
            week_start = current_date
            
            for day_offset in range(7):
                if workouts_scheduled >= training_days:
                    break
                    
                workout_date = week_start + timedelta(days=day_offset)
                
                # Skip weekends if possible (optional logic)
                if workout_date.weekday() in [5, 6] and workouts_scheduled + (7 - day_offset) > training_days:
                    continue
                
                session = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'plan_id': plan_id,
                    'week_number': week_num,
                    'day_number': workouts_scheduled + 1,
                    'scheduled_date': workout_date.isoformat(),
                    'status': 'scheduled'
                }
                
                self.workout_sessions.insert(session)
                workouts_scheduled += 1
            
            current_date = week_start + timedelta(weeks=1)
    
    def get_active_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get currently active plan for user"""
        Acceptance = Query()
        active = self.accepted_plans.search(
            (Acceptance.user_id == user_id) & 
            (Acceptance.status == 'active')
        )
        
        if active:
            # Check if plan is still within 4-week window
            latest = max(active, key=lambda x: x['accepted_at'])
            end_date = datetime.fromisoformat(latest['end_date']).date()
            
            if date.today() <= end_date:
                plan = self.get_plan_by_id(latest['plan_id'])
                plan['acceptance_info'] = latest
                return plan
            else:
                # Mark as completed
                self.accepted_plans.update(
                    {'status': 'completed'},
                    Acceptance.plan_id == latest['plan_id']
                )
        
        return None
    
    def get_next_workout(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get next scheduled workout session"""
        Session = Query()
        today = date.today().isoformat()
        
        upcoming = self.workout_sessions.search(
            (Session.user_id == user_id) &
            (Session.scheduled_date >= today) &
            (Session.status == 'scheduled')
        )
        
        if upcoming:
            return min(upcoming, key=lambda x: x['scheduled_date'])
        return None
    
    def complete_workout_session(self, session_id: str, completion_data: Dict[str, Any]) -> None:
        """Mark workout session as completed with details"""
        Session = Query()
        self.workout_sessions.update(
            {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'exercises_completed': completion_data.get('exercises_completed', []),
                'notes': completion_data.get('notes', ''),
                'duration_minutes': completion_data.get('duration_minutes', 0)
            },
            Session.id == session_id
        )
    
    # Progress photos
    def store_progress_photo(self, user_id: str, photo_data: Dict[str, Any]) -> None:
        """Store progress photo with metrics"""
        photo_data['user_id'] = user_id
        photo_data['uploaded_at'] = datetime.utcnow().isoformat()
        self.progress_photos.insert(photo_data)
    
    def get_progress_photos(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's progress photos ordered by date"""
        Photo = Query()
        photos = self.progress_photos.search(Photo.user_id == user_id)
        return sorted(photos, key=lambda x: x['uploaded_at'], reverse=True)[:limit]
    
    # Plan regeneration
    def store_plan_regeneration(self, original_plan_id: str, new_plan_id: str, comments: str) -> None:
        """Track plan regeneration history"""
        self.plan_regenerations.insert({
            'original_plan_id': original_plan_id,
            'new_plan_id': new_plan_id,
            'comments': comments,
            'regenerated_at': datetime.utcnow().isoformat()
        })
    
    # Analytics helpers
    def get_workout_completion_rate(self, user_id: str, days: int = 30) -> float:
        """Calculate workout completion rate"""
        Session = Query()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        sessions = self.workout_sessions.search(
            (Session.user_id == user_id) &
            (Session.scheduled_date >= cutoff_date)
        )
        
        if not sessions:
            return 0.0
        
        completed = len([s for s in sessions if s.get('status') == 'completed'])
        return (completed / len(sessions)) * 100
    
    def get_plan_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all plans with their acceptance status"""
        Plan = Query()
        user_plans = self.plans.search(Plan.user_id == user_id)
        
        # Enrich with acceptance data
        Acceptance = Query()
        for plan in user_plans:
            acceptance = self.accepted_plans.search(
                (Acceptance.plan_id == plan['id']) &
                (Acceptance.user_id == user_id)
            )
            if acceptance:
                plan['acceptance_info'] = acceptance[0]
        
        return sorted(user_plans, key=lambda x: x['created_at'], reverse=True)