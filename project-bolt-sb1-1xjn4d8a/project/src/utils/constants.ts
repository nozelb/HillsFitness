// Application constants
export const APP_NAME = 'Gym AI Coach';
export const APP_VERSION = '2.0.0';

// API endpoints
export const API_ENDPOINTS = {
  LOGIN: '/login',
  REGISTER: '/register',
  UPLOAD_IMAGE: '/upload-image',
  USER_DATA: '/user-data',
  GENERATE_PLAN: '/generate-plan',
  PLANS: '/plans',
  DASHBOARD: '/dashboard',
  PROGRESS: '/progress',
  PROFILE: '/profile',
  MEASUREMENTS: '/measurements',
  NOTIFICATIONS: '/notifications'
};

// Fitness goals
export const FITNESS_GOALS = {
  LOSE_FAT: { id: 'lose_fat', name: 'Lose Fat', description: 'Reduce body fat while maintaining muscle' },
  GAIN_MUSCLE: { id: 'gain_muscle', name: 'Build Muscle', description: 'Increase muscle mass and strength' },
  STRENGTH: { id: 'strength', name: 'Build Strength', description: 'Focus on increasing strength' },
  RECOMPOSITION: { id: 'recomposition', name: 'Body Recomposition', description: 'Build muscle while losing fat' },
  MAINTENANCE: { id: 'maintenance', name: 'Maintain', description: 'Maintain current physique and health' }
};

// Activity levels
export const ACTIVITY_LEVELS = {
  SEDENTARY: { id: 'sedentary', name: 'Sedentary', description: 'Little to no exercise' },
  LIGHT: { id: 'light', name: 'Light', description: 'Light exercise 1-3 days/week' },
  MODERATE: { id: 'moderate', name: 'Moderate', description: 'Moderate exercise 3-5 days/week' },
  ACTIVE: { id: 'active', name: 'Active', description: 'Heavy exercise 6-7 days/week' },
  ATHLETE: { id: 'athlete', name: 'Athlete', description: 'Very heavy exercise or physical job' }
};

// Experience levels
export const EXPERIENCE_LEVELS = {
  BEGINNER: { id: 'beginner', name: 'Beginner', description: '0-6 months experience' },
  INTERMEDIATE: { id: 'intermediate', name: 'Intermediate', description: '6 months - 2 years' },
  ADVANCED: { id: 'advanced', name: 'Advanced', description: '2+ years experience' }
};

// Chart colors
export const CHART_COLORS = {
  PRIMARY: '#3b82f6',
  SECONDARY: '#8b5cf6',
  SUCCESS: '#10b981',
  WARNING: '#f59e0b',
  DANGER: '#ef4444',
  INFO: '#06b6d4'
};

// Validation rules
export const VALIDATION = {
  MIN_PASSWORD_LENGTH: 8,
  MIN_AGE: 13,
  MAX_AGE: 100,
  MIN_HEIGHT_CM: 100,
  MAX_HEIGHT_CM: 250,
  MIN_WEIGHT_KG: 30,
  MAX_WEIGHT_KG: 300,
  MIN_BODY_FAT: 3,
  MAX_BODY_FAT: 50,
  MIN_TRAINING_DAYS: 3,
  MAX_TRAINING_DAYS: 6,
  MAX_FILE_SIZE_MB: 10
};