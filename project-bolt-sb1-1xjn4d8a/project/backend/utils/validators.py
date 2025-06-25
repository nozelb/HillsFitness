from typing import Dict, List, Any, Optional
import re
from datetime import datetime, date

class Validators:
    """Collection of validation functions for the application"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}# Fixing Missing Files and Errors in Gym AI Coach

## 1. Backend API Files (Empty Files Need Implementation)

### backend/database/migrations.py
```python
from typing import Dict, Any
from datetime import datetime
import json
from tinydb import TinyDB, Query

class DatabaseMigrations:
    def __init__(self, db_path: str = "gym_coach_enhanced.json"):
        self.db = TinyDB(db_path)
        self.migrations_table = self.db.table('migrations')
        
    def get_current_version(self) -> int:
        """Get current database version"""
        Migration = Query()
        migrations = self.migrations_table.all()
        if not migrations:
            return 0
        return max(m['version'] for m in migrations)
    
    def apply_migration(self, version: int, description: str, migration_func):
        """Apply a migration if not already applied"""
        current_version = self.get_current_version()
        
        if version <= current_version:
            print(f"Migration {version} already applied, skipping...")
            return
        
        print(f"Applying migration {version}: {description}")
        try:
            migration_func(self.db)
            self.migrations_table.insert({
                'version': version,
                'description': description,
                'applied_at': datetime.utcnow().isoformat()
            })
            print(f"Migration {version} completed successfully")
        except Exception as e:
            print(f"Migration {version} failed: {e}")
            raise
    
    def run_all_migrations(self):
        """Run all pending migrations"""
        # Migration 1: Add enhanced user profiles
        self.apply_migration(
            version=1,
            description="Add enhanced user profiles structure",
            migration_func=self._migration_1_user_profiles
        )
        
        # Migration 2: Add progress tracking tables
        self.apply_migration(
            version=2,
            description="Add progress tracking tables",
            migration_func=self._migration_2_progress_tracking
        )
        
        # Migration 3: Add notification system
        self.apply_migration(
            version=3,
            description="Add notification and check-in system",
            migration_func=self._migration_3_notifications
        )
        
        # Migration 4: Update plan structure
        self.apply_migration(
            version=4,
            description="Update plan structure to 4-week format",
            migration_func=self._migration_4_plan_structure
        )
    
    def _migration_1_user_profiles(self, db: TinyDB):
        """Create user profiles table structure"""
        # Ensure tables exist
        db.table('user_profiles')
        db.table('user_measurements')
        
        # Migrate existing user_data to new structure if exists
        UserData = Query()
        old_user_data = db.table('user_data').all()
        
        for data in old_user_data:
            # Create measurement record
            measurement = {
                'user_id': data.get('user_id'),
                'version': 1,
                'height_cm': data.get('height'),
                'weight_kg': data.get('weight'),
                'recorded_at': data.get('created_at', datetime.utcnow().isoformat())
            }
            
            # Add smart scale data if available
            if 'smart_scale' in data and data['smart_scale']:
                measurement.update({
                    'body_fat_percentage': data['smart_scale'].get('body_fat_percentage'),
                    'muscle_mass_percentage': data['smart_scale'].get('muscle_percentage'),
                    'visceral_fat': data['smart_scale'].get('visceral_fat')
                })
            
            db.table('user_measurements').insert(measurement)
    
    def _migration_2_progress_tracking(self, db: TinyDB):
        """Create progress tracking tables"""
        db.table('progress_entries')
        db.table('progress_photos')
        db.table('workout_logs')
        db.table('weight_logs')
        db.table('body_measurements')
    
    def _migration_3_notifications(self, db: TinyDB):
        """Create notification system tables"""
        db.table('check_ins')
        db.table('notifications')
    
    def _migration_4_plan_structure(self, db: TinyDB):
        """Update plan structure to new 4-week format"""
        db.table('plan_sessions')
        db.table('plan_feedback')
        
        # Update existing plans if needed
        Plan = Query()
        old_plans = db.table('plans').all()
        
        for plan in old_plans:
            if 'version' not in plan:
                # Add versioning to old plans
                db.table('plans').update(
                    {'version': 1, 'status': 'completed'},
                    Plan.id == plan['id']
                )

# Run migrations when module is imported
if __name__ == "__main__":
    migrator = DatabaseMigrations()
    migrator.run_all_migrations()