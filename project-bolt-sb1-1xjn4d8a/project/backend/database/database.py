# backend/database/database.py - Enhanced database with versioning and new features

from tinydb import TinyDB, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import uuid
import json
from .models import (
    UserProfile, UserMeasurements, CompletePlan, ProgressEntry, 
    CheckIn, PlanStatus, CheckInType
)

class EnhancedGymDatabase:
    def __init__(self, db_path: str = "gym_coach_enhanced.json"):
        self.db = TinyDB(db_path)
        
        # Authentication
        self.users = self.db.table('users')
        
        # Core user data (versioned)
        self.user_profiles = self.db.table('user_profiles')
        self.user_measurements = self.db.table('user_measurements')
        
        # Plans (versioned with 4-week structure)
        self.plans = self.db.table('plans')
        self.plan_sessions = self.db.table('plan_sessions')
        self.plan_feedback = self.db.table('plan_feedback')
        
        # Progress tracking
        self.progress_entries = self.db.table('progress_entries')
        self.progress_photos = self.db.table('progress_photos')
        
        # Check-ins and notifications
        self.check_ins = self.db.table('check_ins')
        self.notifications = self.db.table('notifications')
        
        # Legacy tables (for backward compatibility)
        self.user_data = self.db.table('user_data')
        self.image_analyses = self.db.table('image_analyses')
        self.workout_logs = self.db.table('workout_logs')
        self.weight_logs = self.db.table('weight_logs')
        self.body_measurements = self.db.table('body_measurements')

    # ============ USER AUTHENTICATION ============
    def create_user(self, user_data: Dict[str, Any]) -> None:
        """Create new user account"""
        self.users.insert(user_data)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email for authentication"""
        User = Query()
        result = self.users.search(User.email == email)
        return result[0] if result else None

    # ============ USER PROFILE MANAGEMENT ============
    def create_or_update_profile(self, profile: UserProfile) -> str:
        """Create or update user profile (static data)"""
        Profile = Query()
        existing = self.user_profiles.search(Profile.user_id == profile.user_id)
        
        profile_dict = profile.dict()
        profile_dict['updated_at'] = datetime.utcnow().isoformat()
        
        if existing:
            # Update existing profile
            self.user_profiles.update(profile_dict, Profile.user_id == profile.user_id)
            return existing[0].get('id', str(uuid.uuid4()))
        else:
            # Create new profile
            profile_dict['id'] = str(uuid.uuid4())
            profile_dict['created_at'] = datetime.utcnow().isoformat()
            self.user_profiles.insert(profile_dict)
            return profile_dict['id']
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile with calculated age"""
        Profile = Query()
        result = self.user_profiles.search(Profile.user_id == user_id)
        
        if result:
            profile_data = result[0]
            try:
                return UserProfile(**profile_data)
            except Exception as e:
                print(f"Error parsing profile: {e}")
                return None
        return None
    
    def is_profile_complete(self, user_id: str) -> bool:
        """Check if user has completed their profile setup"""
        profile = self.get_user_profile(user_id)
        return profile is not None

    # ============ MEASUREMENTS TRACKING ============
    def store_measurements(self, measurements: UserMeasurements) -> str:
        """Store user measurements with versioning"""
        # Get the latest version number
        Measurement = Query()
        existing = self.user_measurements.search(Measurement.user_id == measurements.user_id)
        
        if existing:
            latest_version = max(m.get('version', 1) for m in existing)
            measurements.version = latest_version + 1
        else:
            measurements.version = 1
        
        measurement_dict = measurements.dict()
        measurement_dict['id'] = str(uuid.uuid4())
        measurement_dict['recorded_at'] = datetime.utcnow().isoformat()
        
        self.user_measurements.insert(measurement_dict)
        return measurement_dict['id']
    
    def get_latest_measurements(self, user_id: str) -> Optional[UserMeasurements]:
        """Get the most recent measurements for a user"""
        Measurement = Query()
        results = self.user_measurements.search(Measurement.user_id == user_id)
        
        if results:
            latest = max(results, key=lambda x: x.get('version', 1))
            try:
                return UserMeasurements(**latest)
            except Exception as e:
                print(f"Error parsing measurements: {e}")
                return None
        return None
    
    def get_measurements_history(self, user_id: str, limit: int = 10) -> List[UserMeasurements]:
        """Get measurement history for tracking changes"""
        Measurement = Query()
        results = self.user_measurements.search(Measurement.user_id == user_id)
        
        # Sort by version descending and limit
        sorted_results = sorted(results, key=lambda x: x.get('version', 1), reverse=True)[:limit]
        
        measurements = []
        for result in sorted_results:
            try:
                measurements.append(UserMeasurements(**result))
            except Exception as e:
                print(f"Error parsing measurement in history: {e}")
                continue
        
        return measurements

    # ============ PLAN MANAGEMENT (4-WEEK VERSIONED) ============
    def store_plan(self, plan: CompletePlan) -> str:
        """Store a complete 4-week plan with versioning"""
        # Get the latest version number for this user
        Plan = Query()
        existing = self.plans.search(Plan.user_id == plan.user_id)
        
        if existing:
            latest_version = max(p.get('version', 1) for p in existing)
            plan.version = latest_version + 1
        else:
            plan.version = 1
        
        plan_dict = plan.dict()
        plan_dict['id'] = str(uuid.uuid4())
        plan_dict['created_at'] = datetime.utcnow().isoformat()
        
        self.plans.insert(plan_dict)
        
        # Create check-ins for this plan
        self._create_plan_checkins(plan.user_id, plan_dict['id'])
        
        return plan_dict['id']
    
    def get_plan_by_id(self, plan_id: str) -> Optional[CompletePlan]:
        """Get a specific plan by ID"""
        Plan = Query()
        result = self.plans.search(Plan.id == plan_id)
        
        if result:
            try:
                return CompletePlan(**result[0])
            except Exception as e:
                print(f"Error parsing plan: {e}")
                return None
        return None
    
    def get_active_plan(self, user_id: str) -> Optional[CompletePlan]:
        """Get the user's currently active plan"""
        Plan = Query()
        active_plans = self.plans.search(
            (Plan.user_id == user_id) & (Plan.status == PlanStatus.ACTIVE.value)
        )
        
        if active_plans:
            # Get the most recent active plan
            latest = max(active_plans, key=lambda x: x.get('created_at', ''))
            try:
                return CompletePlan(**latest)
            except Exception as e:
                print(f"Error parsing active plan: {e}")
                return None
        return None
    
    def get_plan_history(self, user_id: str, limit: int = 20) -> List[CompletePlan]:
        """Get user's plan history"""
        Plan = Query()
        results = self.plans.search(Plan.user_id == user_id)
        
        # Sort by created_at descending
        sorted_results = sorted(results, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]
        
        plans = []
        for result in sorted_results:
            try:
                plans.append(CompletePlan(**result))
            except Exception as e:
                print(f"Error parsing plan in history: {e}")
                continue
        
        return plans
    
    def accept_plan(self, plan_id: str) -> bool:
        """Mark a plan as accepted and activate it"""
        Plan = Query()
        plan = self.plans.search(Plan.id == plan_id)
        
        if plan:
            # Deactivate any other active plans for this user
            user_id = plan[0]['user_id']
            self.plans.update(
                {'status': PlanStatus.COMPLETED.value},
                (Plan.user_id == user_id) & (Plan.status == PlanStatus.ACTIVE.value)
            )
            
            # Activate this plan
            self.plans.update(
                {
                    'status': PlanStatus.ACTIVE.value,
                    'accepted_at': datetime.utcnow().isoformat(),
                    'approved_by_user': True
                },
                Plan.id == plan_id
            )
            
            return True
        return False
    
    def regenerate_plan(self, original_plan_id: str, new_plan: CompletePlan, feedback: str) -> str:
        """Create a regenerated version of a plan"""
        new_plan.parent_plan_id = original_plan_id
        new_plan.regeneration_reason = feedback
        new_plan.status = PlanStatus.DRAFT
        
        # Mark original as regenerated
        Plan = Query()
        self.plans.update(
            {'status': PlanStatus.REGENERATED.value},
            Plan.id == original_plan_id
        )
        
        return self.store_plan(new_plan)

    # ============ PROGRESS TRACKING ============
    def store_progress_entry(self, progress: ProgressEntry) -> str:
        """Store a progress entry"""
        progress_dict = progress.dict()
        progress_dict['id'] = str(uuid.uuid4())
        progress_dict['recorded_at'] = datetime.utcnow().isoformat()
        
        self.progress_entries.insert(progress_dict)
        return progress_dict['id']
    
    def get_progress_history(self, user_id: str, days: int = 90) -> List[ProgressEntry]:
        """Get progress history for a user"""
        Progress = Query()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        results = self.progress_entries.search(
            (Progress.user_id == user_id) & (Progress.recorded_at >= cutoff)
        )
        
        progress_list = []
        for result in results:
            try:
                progress_list.append(ProgressEntry(**result))
            except Exception as e:
                print(f"Error parsing progress entry: {e}")
                continue
        
        return sorted(progress_list, key=lambda x: x.recorded_at, reverse=True)
    
    def get_latest_progress(self, user_id: str) -> Optional[ProgressEntry]:
        """Get the most recent progress entry"""
        progress_list = self.get_progress_history(user_id, days=30)
        return progress_list[0] if progress_list else None

    # ============ CHECK-INS AND NOTIFICATIONS ============
    def _create_plan_checkins(self, user_id: str, plan_id: str) -> None:
        """Create automatic check-ins for a new plan"""
        start_date = date.today()
        
        # Weekly weight check-ins for 4 weeks
        for week in range(4):
            checkin_date = start_date + timedelta(weeks=week)
            checkin = CheckIn(
                user_id=user_id,
                type=CheckInType.WEEKLY_WEIGHT,
                title=f"Week {week + 1} Weight Check-in",
                description="Record your weight and how you're feeling this week",
                due_date=checkin_date
            )
            self.store_checkin(checkin)
        
        # Progress photo check-ins (weeks 2 and 4)
        for week in [1, 3]:
            checkin_date = start_date + timedelta(weeks=week)
            checkin = CheckIn(
                user_id=user_id,
                type=CheckInType.PROGRESS_PHOTO,
                title=f"Week {week + 1} Progress Photo",
                description="Take a progress photo to track your visual changes",
                due_date=checkin_date
            )
            self.store_checkin(checkin)
        
        # Plan completion check-in
        completion_date = start_date + timedelta(weeks=4)
        checkin = CheckIn(
            user_id=user_id,
            type=CheckInType.PLAN_COMPLETION,
            title="Plan Completion Review",
            description="Review your 4-week plan results and plan your next steps",
            due_date=completion_date
        )
        self.store_checkin(checkin)
    
    def store_checkin(self, checkin: CheckIn) -> str:
        """Store a check-in"""
        checkin_dict = checkin.dict()
        checkin_dict['id'] = str(uuid.uuid4())
        checkin_dict['created_at'] = datetime.utcnow().isoformat()
        
        self.check_ins.insert(checkin_dict)
        return checkin_dict['id']
    
    def get_pending_checkins(self, user_id: str) -> List[CheckIn]:
        """Get pending check-ins for a user"""
        CheckInQuery = Query()
        results = self.check_ins.search(
            (CheckInQuery.user_id == user_id) & 
            (CheckInQuery.status == 'pending') &
            (CheckInQuery.due_date <= date.today().isoformat())
        )
        
        checkins = []
        for result in results:
            try:
                checkins.append(CheckIn(**result))
            except Exception as e:
                print(f"Error parsing check-in: {e}")
                continue
        
        return sorted(checkins, key=lambda x: x.due_date)
    
    def complete_checkin(self, checkin_id: str, response_data: Dict[str, Any]) -> bool:
        """Mark a check-in as completed"""
        CheckInQuery = Query()
        self.check_ins.update(
            {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'response_data': response_data
            },
            CheckInQuery.id == checkin_id
        )
        return True

    # ============ DASHBOARD AND ANALYTICS ============
    def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        # Current plan
        active_plan = self.get_active_plan(user_id)
        
        # Recent progress
        recent_progress = self.get_progress_history(user_id, days=30)
        
        # Pending check-ins
        pending_checkins = self.get_pending_checkins(user_id)
        
        # Weekly stats
        weekly_stats = self._calculate_weekly_stats(user_id)
        
        # Progress charts data
        chart_data = self._get_chart_data(user_id)
        
        # Next workout (if plan is active)
        next_workout = None
        if active_plan:
            next_workout = self._get_next_workout(active_plan)
        
        return {
            'active_plan': active_plan.dict() if active_plan else None,
            'recent_progress': [p.dict() for p in recent_progress[:5]],
            'pending_checkins': [c.dict() for c in pending_checkins],
            'weekly_stats': weekly_stats,
            'chart_data': chart_data,
            'next_workout': next_workout,
            'profile_complete': self.is_profile_complete(user_id)
        }
    
    def _calculate_weekly_stats(self, user_id: str) -> Dict[str, Any]:
        """Calculate weekly statistics"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get recent progress entries
        Progress = Query()
        recent_entries = self.progress_entries.search(
            (Progress.user_id == user_id) & 
            (Progress.recorded_at >= week_ago.isoformat())
        )
        
        # Calculate averages
        total_workouts = sum(1 for entry in recent_entries if entry.get('workouts_completed_week', 0) > 0)
        avg_energy = sum(entry.get('energy_level', 0) for entry in recent_entries) / max(len(recent_entries), 1)
        avg_mood = sum(entry.get('mood_rating', 0) for entry in recent_entries) / max(len(recent_entries), 1)
        
        return {
            'workouts_this_week': total_workouts,
            'avg_energy_level': round(avg_energy, 1),
            'avg_mood': round(avg_mood, 1),
            'checkins_completed': len([c for c in recent_entries if c.get('recorded_at')]),
            'streak_days': self._calculate_streak(user_id)
        }
    
    def _get_chart_data(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get data for dashboard charts"""
        # Weight trend (last 3 months)
        measurements = self.get_measurements_history(user_id, limit=20)
        weight_data = [
            {
                'date': m.recorded_at.isoformat()[:10] if hasattr(m.recorded_at, 'isoformat') else str(m.recorded_at)[:10],
                'weight': m.weight_kg,
                'body_fat': m.body_fat_percentage
            }
            for m in reversed(measurements)
        ]
        
        # Progress trend
        progress = self.get_progress_history(user_id, days=90)
        progress_data = [
            {
                'date': p.recorded_at.isoformat()[:10] if hasattr(p.recorded_at, 'isoformat') else str(p.recorded_at)[:10],
                'energy': p.energy_level,
                'mood': p.mood_rating,
                'sleep': p.sleep_hours
            }
            for p in reversed(progress[-30:])  # Last 30 entries
        ]
        
        return {
            'weight_trend': weight_data,
            'progress_trend': progress_data,
            'workout_frequency': self._get_workout_frequency_data(user_id)
        }
    
    def _get_workout_frequency_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get workout frequency data for charts"""
        # This would integrate with actual workout completion tracking
        # For now, return sample data structure
        weeks = []
        for i in range(4):
            week_start = datetime.utcnow() - timedelta(weeks=i+1)
            weeks.append({
                'week': f'Week {4-i}',
                'planned_workouts': 4,
                'completed_workouts': 3,  # This would come from actual tracking
                'completion_rate': 75
            })
        return weeks
    
    def _calculate_streak(self, user_id: str) -> int:
        """Calculate current streak of consistent progress logging"""
        progress = self.get_progress_history(user_id, days=30)
        
        if not progress:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for i in range(30):  # Check last 30 days
            check_date = current_date - timedelta(days=i)
            
            # Check if there's a progress entry for this date
            day_entries = [
                p for p in progress 
                if p.recorded_at.date() == check_date if hasattr(p.recorded_at, 'date') 
                else datetime.fromisoformat(str(p.recorded_at)).date() == check_date
            ]
            
            if day_entries:
                streak += 1
            else:
                break
        
        return streak
    
    def _get_next_workout(self, plan: CompletePlan) -> Optional[Dict[str, Any]]:
        """Get the next scheduled workout from active plan"""
        if not plan.workout_weeks:
            return None
        
        # Simple logic: cycle through weeks and days
        # In a full implementation, this would track actual completion
        current_week = plan.workout_weeks[0]  # Start with week 1
        
        if current_week.workouts:
            next_workout = current_week.workouts[0]
            return {
                'week_number': current_week.week_number,
                'day_name': next_workout.day_name,
                'muscle_groups': next_workout.muscle_groups,
                'estimated_duration': next_workout.estimated_duration_minutes,
                'exercise_count': len(next_workout.exercises)
            }
        
        return None

    # ============ LEGACY COMPATIBILITY METHODS ============
    def store_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Legacy method for backward compatibility"""
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow().isoformat()
        self.user_data.insert(data)
    
    def get_latest_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        UserData = Query()
        results = self.user_data.search(UserData.user_id == user_id)
        return max(results, key=lambda x: x['created_at']) if results else None
    
    def store_image_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        """Legacy method for backward compatibility"""
        analysis['user_id'] = user_id
        analysis['created_at'] = datetime.utcnow().isoformat()
        self.image_analyses.insert(analysis)
    
    def get_latest_image_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        Analysis = Query()
        results = self.image_analyses.search(Analysis.user_id == user_id)
        return max(results, key=lambda x: x['created_at']) if results else None