# services/plan_service.py
class PlanService:
    def generate_4_week_plan(self, user_id: str, measurements: dict) -> Plan
    def regenerate_plan(self, plan_id: str, feedback: str) -> Plan
    def accept_plan(self, plan_id: str) -> None
    def get_active_plan(self, user_id: str) -> Plan
    def get_plan_history(self, user_id: str) -> List[Plan]
    def calculate_progressive_overload(self, week: int, exercise: dict) -> dict
    def ensure_minimum_exercises(self, workout_day: dict) -> dict
    def apply_safety_limits(self, nutrition_plan: dict) -> dict
