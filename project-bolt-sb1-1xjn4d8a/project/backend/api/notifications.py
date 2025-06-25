from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from database.models import CheckIn, CheckInType
from database.database import EnhancedGymDatabase
import uuid

class NotificationService:
    def __init__(self, db: EnhancedGymDatabase):
        self.db = db
    
    def create_plan_notifications(self, user_id: str, plan_id: str) -> List[str]:
        """Create all notifications for a new plan"""
        notification_ids = []
        start_date = date.today()
        
        # Weekly weight check-ins
        for week in range(4):
            checkin_date = start_date + timedelta(weeks=week+1)
            checkin = CheckIn(
                user_id=user_id,
                type=CheckInType.WEEKLY_WEIGHT,
                title=f"Week {week + 1} Weight Check-in",
                description="Time to record your weight and measurements for the week",
                due_date=checkin_date
            )
            checkin_id = self.db.store_checkin(checkin)
            notification_ids.append(checkin_id)
        
        # Progress photos (weeks 2 and 4)
        for week in [2, 4]:
            photo_date = start_date + timedelta(weeks=week)
            checkin = CheckIn(
                user_id=user_id,
                type=CheckInType.PROGRESS_PHOTO,
                title=f"Week {week} Progress Photo",
                description="Take front and side photos to track your visual progress",
                due_date=photo_date
            )
            checkin_id = self.db.store_checkin(checkin)
            notification_ids.append(checkin_id)
        
        # Mid-plan feedback
        feedback_date = start_date + timedelta(weeks=2)
        checkin = CheckIn(
            user_id=user_id,
            type=CheckInType.PLAN_FEEDBACK,
            title="Mid-Plan Feedback",
            description="How is the plan working for you? Any adjustments needed?",
            due_date=feedback_date
        )
        checkin_id = self.db.store_checkin(checkin)
        notification_ids.append(checkin_id)
        
        # Plan completion
        completion_date = start_date + timedelta(weeks=4)
        checkin = CheckIn(
            user_id=user_id,
            type=CheckInType.PLAN_COMPLETION,
            title="Plan Completion Review",
            description="Congratulations on completing your 4-week plan! Time to review your progress and plan next steps.",
            due_date=completion_date
        )
        checkin_id = self.db.store_checkin(checkin)
        notification_ids.append(checkin_id)
        
        return notification_ids
    
    def get_upcoming_notifications(self, user_id: str, days_ahead: int = 7) -> List[CheckIn]:
        """Get notifications due in the next N days"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        all_checkins = self.db.get_pending_checkins(user_id)
        
        upcoming = [
            checkin for checkin in all_checkins
            if checkin.due_date <= cutoff_date
        ]
        
        return sorted(upcoming, key=lambda x: x.due_date)
    
    def get_overdue_notifications(self, user_id: str) -> List[CheckIn]:
        """Get overdue notifications"""
        all_checkins = self.db.get_pending_checkins(user_id)
        today = date.today()
        
        overdue = [
            checkin for checkin in all_checkins
            if checkin.due_date < today and checkin.status == 'pending'
        ]
        
        return sorted(overdue, key=lambda x: x.due_date)
    
    def mark_notification_completed(self, checkin_id: str, response_data: Dict[str, Any]) -> bool:
        """Mark a notification as completed with user response"""
        return self.db.complete_checkin(checkin_id, response_data)
    
    def send_reminder_email(self, user_email: str, checkin: CheckIn) -> bool:
        """Send reminder email (placeholder for email integration)"""
        # In production, integrate with email service (SendGrid, AWS SES, etc.)
        print(f"Would send email to {user_email} for {checkin.title}")
        return True
    
    def create_custom_reminder(self, user_id: str, title: str, description: str, 
                             due_date: date, type: CheckInType = CheckInType.WELLNESS_CHECK) -> str:
        """Create a custom reminder for user"""
        checkin = CheckIn(
            user_id=user_id,
            type=type,
            title=title,
            description=description,
            due_date=due_date
        )
        return self.db.store_checkin(checkin)
    
    def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for user"""
        from tinydb import Query
        CheckInQuery = Query()
        
        all_checkins = self.db.check_ins.search(CheckInQuery.user_id == user_id)
        
        completed = [c for c in all_checkins if c.get('status') == 'completed']
        pending = [c for c in all_checkins if c.get('status') == 'pending']
        overdue = [c for c in pending if c.get('due_date') and 
                   datetime.fromisoformat(c['due_date']).date() < date.today()]
        
        return {
            "total_notifications": len(all_checkins),
            "completed": len(completed),
            "pending": len(pending),
            "overdue": len(overdue),
            "completion_rate": len(completed) / len(all_checkins) if all_checkins else 0,
            "types": {
                "weight_checkins": len([c for c in all_checkins if c.get('type') == CheckInType.WEEKLY_WEIGHT.value]),
                "progress_photos": len([c for c in all_checkins if c.get('type') == CheckInType.PROGRESS_PHOTO.value]),
                "feedback": len([c for c in all_checkins if c.get('type') == CheckInType.PLAN_FEEDBACK.value])
            }
        }