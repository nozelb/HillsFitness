from __future__ import annotations

from datetime import date
from typing import Any, Dict, List
import re

class Validators:
    """Collection of reusable validation helpers."""

    EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    
    @staticmethod
    def validate_email(email: str) -> bool:
                """Return ``True`` if ``email`` is in a valid format."""
        return bool(Validators.EMAIL_REGEX.match(email))

    @staticmethod
    def validate_password(password: str) -> List[str]:
        """Validate password strength and return a list of issues."""
        issues: List[str] = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            issues.append("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            issues.append("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            issues.append(
                "Password must contain at least one special character"
            )

        return issues

    @staticmethod
    def validate_measurements(measurements: Dict[str, Any]) -> List[str]:
        """Validate body measurement values."""
        errors: List[str] = []

        height = measurements.get("height_cm")
        if height is not None:
            if not isinstance(height, (int, float)):
                errors.append("Height must be a number")
            elif height < 100 or height > 250:
                errors.append("Height must be between 100-250 cm")

        weight = measurements.get("weight_kg")
        if weight is not None:
            if not isinstance(weight, (int, float)):
                errors.append("Weight must be a number")
            elif weight < 30 or weight > 300:
                errors.append("Weight must be between 30-300 kg")

        body_fat = measurements.get("body_fat_percentage")
        if body_fat is not None:
            if not isinstance(body_fat, (int, float)):
                errors.append("Body fat percentage must be a number")
            elif body_fat < 3 or body_fat > 50:
                errors.append("Body fat percentage must be between 3-50%")

        muscle_mass = measurements.get("muscle_mass_percentage")
        if muscle_mass is not None:
            if not isinstance(muscle_mass, (int, float)):
                errors.append("Muscle mass percentage must be a number")
            elif muscle_mass < 20 or muscle_mass > 60:
                errors.append("Muscle mass percentage must be between 20-60%")

        visceral_fat = measurements.get("visceral_fat")
        if visceral_fat is not None:
            if not isinstance(visceral_fat, (int, float)):
                errors.append("Visceral fat must be a number")
            elif visceral_fat < 1 or visceral_fat > 30:
                errors.append("Visceral fat must be between 1-30")

        return errors

    @staticmethod
    def validate_profile_data(profile_data: Dict[str, Any]) -> List[str]:
        """Validate user profile information."""
        errors: List[str] = []

        required_fields = [
            "full_name",
            "date_of_birth",
            "sex",
            "primary_fitness_goal",
        ]
        for field in required_fields:
            if not profile_data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")

        full_name = profile_data.get("full_name", "")
        if full_name and (len(full_name) < 2 or len(full_name) > 100):
            errors.append("Full name must be between 2-100 characters")

        dob = profile_data.get("date_of_birth")
        if dob:
            try:
                if isinstance(dob, str):
                    dob_date = date.fromisoformat(dob)
                else:
                    dob_date = dob

                age = Validators._calculate_age(dob_date)
                if age < 13:
                    errors.append("Must be at least 13 years old")
                elif age > 100:
                    errors.append("Age must be less than 100 years")
            except (ValueError, TypeError):
                errors.append("Invalid date of birth format (use YYYY-MM-DD)")

        sex = profile_data.get("sex")
        if sex and sex not in ["male", "female"]:
            errors.append("Sex must be 'male' or 'female'")

        valid_goals = [
            "lose_fat",
            "gain_muscle",
            "strength",
            "recomposition",
            "maintenance",
        ]
        goal = profile_data.get("primary_fitness_goal")
        if goal and goal not in valid_goals:
            errors.append(
                f"Invalid fitness goal. Must be one of: {', '.join(valid_goals)}"
            )

        training_days = profile_data.get("preferred_training_days")
        if training_days is not None:
            if not isinstance(training_days, int):
                errors.append("Training days must be a number")
            elif training_days < 3 or training_days > 6:
                errors.append("Training days must be between 3-6 days per week")

        valid_activity_levels = [
            "sedentary",
            "light",
            "moderate",
            "active",
            "athlete",
        ]
        activity_level = profile_data.get("activity_level")
        if activity_level and activity_level not in valid_activity_levels:
            errors.append(
                "Invalid activity level. Must be one of: "
                f"{', '.join(valid_activity_levels)}"
            )

        valid_experience = ["beginner", "intermediate", "advanced"]
        experience = profile_data.get("gym_experience")
        if experience and experience not in valid_experience:
            errors.append(
                "Invalid experience level. Must be one of: "
                f"{', '.join(valid_experience)}"
            )

        return errors

    @staticmethod
    def _calculate_age(date_of_birth: date) -> int:
        """Return age in years from ``date_of_birth``."""
        today = date.today()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )