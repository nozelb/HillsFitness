# services/plan_service.py
class PlanService:
    def generate_4_week_plan(self, user_id: str, measurements: dict) -> "Plan":
        """Generate a new 4 week plan"""
        pass

    def regenerate_plan(self, plan_id: str, feedback: str) -> "Plan":
        """Regenerate an existing plan with feedback"""
        pass

    def accept_plan(self, plan_id: str) -> None:
        """Mark a plan as accepted by the user"""
        pass

    def get_active_plan(self, user_id: str) -> "Plan":
        """Return the currently active plan for the user"""
        pass

    def get_plan_history(self, user_id: str) -> List["Plan"]:
        """Return a list of the user's previous plans"""
        return []

    def calculate_progressive_overload(self, week: int, exercise: dict) -> dict:
        """Calculate progressive overload for an exercise"""
        return {}

    def ensure_minimum_exercises(self, workout_day: dict) -> dict:
        """Ensure a workout has the minimum required exercises"""
        return workout_day

    def apply_safety_limits(self, nutrition_plan: dict) -> dict:
        """Apply basic safety limits to a nutrition plan"""
        return nutrition_plan
