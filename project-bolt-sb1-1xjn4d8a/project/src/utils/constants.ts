// src/utils/constants.ts - Updated for Specification Compliance
export const APP_NAME = 'Gym AI Coach';
export const APP_VERSION = '2.1.0';
export const APP_DESCRIPTION = 'AI-powered fitness coach with advanced computer vision';

// Enhanced API endpoints matching exact specification
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: '/api/login',
  REGISTER: '/api/register',
  
  // Profile management (STATIC - persisted once)
  PROFILE: '/api/profile',
  CREATE_PROFILE: '/api/profile',
  UPDATE_PROFILE: '/api/profile',
  
  // Plan generation workflow (DYNAMIC - each time)
  WIZARD_DATA: '/api/wizard-data',
  UPLOAD_ANALYZE_IMAGE: '/api/upload-analyze-image',
  GENERATE_PLAN: '/api/generate-plan',
  
  // Plan management
  ACCEPT_PLAN: '/api/accept-plan',
  REGENERATE_PLAN: '/api/regenerate-plan',
  PLANS: '/api/plans',
  
  // Progress tracking and compliance
  LOG_SESSION: '/api/log-session',
  DASHBOARD: '/api/dashboard',
  PROGRESS_CHARTS: '/api/progress-charts',
  
  // Legacy endpoints (keep for backward compatibility)
  USER_DATA: '/api/user-data',
  UPLOAD_IMAGE: '/api/upload-image',
  MEASUREMENTS: '/api/measurements',
  NOTIFICATIONS: '/api/notifications'
} as const;

// Fitness goals matching specification format
export const FITNESS_GOALS = {
  MUSCLE_GAIN: { 
    id: 'muscle-gain', 
    name: 'Build Muscle', 
    description: 'Increase muscle mass and strength',
    calories_modifier: 1.10,
    protein_emphasis: 'high'
  },
  FAT_LOSS: { 
    id: 'fat-loss', 
    name: 'Lose Fat', 
    description: 'Reduce body fat while preserving muscle',
    calories_modifier: 0.85,
    protein_emphasis: 'high'
  },
  RECOMP: { 
    id: 'recomp', 
    name: 'Body Recomposition', 
    description: 'Build muscle while losing fat simultaneously',
    calories_modifier: 1.00,
    protein_emphasis: 'very_high'
  },
  MAINTENANCE: { 
    id: 'maintenance', 
    name: 'Maintain', 
    description: 'Maintain current physique and health',
    calories_modifier: 1.00,
    protein_emphasis: 'moderate'
  }
} as const;

// Activity levels matching specification
export const ACTIVITY_LEVELS = {
  SEDENTARY: { 
    id: 'sedentary', 
    name: 'Sedentary', 
    description: 'Little to no exercise',
    multiplier: 1.2
  },
  LIGHT: { 
    id: 'light', 
    name: 'Light', 
    description: 'Light exercise 1-3 days/week',
    multiplier: 1.375
  },
  MODERATE: { 
    id: 'moderate', 
    name: 'Moderate', 
    description: 'Moderate exercise 3-5 days/week',
    multiplier: 1.55
  },
  HIGH: { 
    id: 'high', 
    name: 'High', 
    description: 'Heavy exercise 6-7 days/week',
    multiplier: 1.725
  }
} as const;

// Sex options matching specification
export const SEX_OPTIONS = {
  MALE: { id: 'male', name: 'Male', icon: '♂️' },
  FEMALE: { id: 'female', name: 'Female', icon: '♀️' },
  NON_BINARY: { id: 'non-binary', name: 'Non-binary', icon: '⚧️' }
} as const;

// Training days options
export const TRAINING_DAYS = [
  { value: 1, label: '1 day/week', description: 'Minimal maintenance' },
  { value: 2, label: '2 days/week', description: 'Light activity' },
  { value: 3, label: '3 days/week', description: 'Standard beginner' },
  { value: 4, label: '4 days/week', description: 'Intermediate' },
  { value: 5, label: '5 days/week', description: 'Advanced' },
  { value: 6, label: '6 days/week', description: 'Very advanced' },
  { value: 7, label: '7 days/week', description: 'Elite/athlete' }
] as const;

// Equipment limitations options
export const EQUIPMENT_LIMITS = {
  NO_BARBELL: 'no barbell',
  NO_DUMBBELLS: 'no dumbbells',
  NO_MACHINES: 'no machines',
  BODYWEIGHT_ONLY: 'bodyweight only',
  RESISTANCE_BANDS_ONLY: 'resistance bands only',
  HOME_GYM: 'home gym setup',
  MINIMAL_EQUIPMENT: 'minimal equipment'
} as const;

// Common injury types for dropdown
export const COMMON_INJURIES = [
  'right-knee meniscus',
  'left-knee meniscus',
  'lower back strain',
  'shoulder impingement',
  'tennis elbow',
  'wrist pain',
  'ankle sprain',
  'hip flexor strain',
  'neck pain',
  'rotator cuff'
] as const;

// Posture alerts that can be detected
export const POSTURE_ALERTS = {
  ROUNDED_SHOULDERS: {
    id: 'rounded_shoulders',
    name: 'Rounded Shoulders',
    description: 'Shoulders roll forward from proper alignment',
    corrective_exercises: ['face-pulls', 'doorway-stretch', 'wall-angels']
  },
  ANTERIOR_PELVIC_TILT: {
    id: 'anterior_pelvic_tilt',
    name: 'Anterior Pelvic Tilt',
    description: 'Pelvis tilts forward causing lower back arch',
    corrective_exercises: ['hip-flexor-stretch', 'dead-bug', 'glute-bridge']
  },
  FORWARD_HEAD: {
    id: 'forward_head',
    name: 'Forward Head Posture',
    description: 'Head positioned forward of shoulders',
    corrective_exercises: ['chin-tucks', 'neck-strengthening']
  },
  ASYMMETRIC_SHOULDERS: {
    id: 'asymmetric_shoulders',
    name: 'Uneven Shoulders',
    description: 'One shoulder higher than the other',
    corrective_exercises: ['unilateral-stretching', 'postural-awareness']
  },
  KNEE_VALGUS: {
    id: 'knee_valgus',
    name: 'Knee Valgus',
    description: 'Knees cave inward during movement',
    corrective_exercises: ['glute-strengthening', 'hip-abduction']
  }
} as const;

// Enhanced validation rules matching specification
export const VALIDATION = {
  // Age validation
  MIN_AGE: 13,
  MAX_AGE: 100,
  KID_SAFE_AGE: 13, // No calorie counting below this age
  
  // Physical measurements (metric only)
  MIN_HEIGHT_CM: 100,
  MAX_HEIGHT_CM: 230,
  MIN_WEIGHT_KG: 30,
  MAX_WEIGHT_KG: 300,
  
  // Body composition
  MIN_BODY_FAT: 3,
  MAX_BODY_FAT: 60,
  MIN_MUSCLE_PCT: 20,
  MAX_MUSCLE_PCT: 70,
  MIN_VISCERAL_FAT: 1,
  MAX_VISCERAL_FAT: 30,
  
  // Training parameters
  MIN_TRAINING_DAYS: 1,
  MAX_TRAINING_DAYS: 7,
  
  // File upload
  MAX_FILE_SIZE_MB: 10,
  MIN_IMAGE_QUALITY: 0.70, // Critical threshold
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/jpg'],
  
  // Text inputs
  MIN_PASSWORD_LENGTH: 8,
  MAX_COMMENT_LENGTH: 500,
  MAX_NAME_LENGTH: 100
} as const;

// Metric unit conversions
export const UNIT_CONVERSIONS = {
  // Length
  CM_TO_INCHES: 0.393701,
  INCHES_TO_CM: 2.54,
  
  // Weight  
  KG_TO_LBS: 2.20462,
  LBS_TO_KG: 0.453592,
  
  // Energy
  KJ_TO_KCAL: 0.239006,
  KCAL_TO_KJ: 4.184,
  
  // Volume
  ML_TO_FL_OZ: 0.033814,
  FL_OZ_TO_ML: 29.5735
} as const;

// Default macro percentages (adjustable ±5% per specification)
export const DEFAULT_MACROS = {
  PROTEIN_PCT: 0.30, // 30% of kJ
  CARBS_PCT: 0.45,   // 45% of kJ  
  FAT_PCT: 0.25      // 25% of kJ
} as const;

// Plan status types
export const PLAN_STATUS = {
  DRAFT: 'draft',
  ACTIVE: 'active', 
  COMPLETED: 'completed',
  ABANDONED: 'abandoned',
  REGENERATING: 'regenerating'
} as const;

// Session status types
export const SESSION_STATUS = {
  SCHEDULED: 'scheduled',
  COMPLETED: 'completed',
  SKIPPED: 'skipped',
  IN_PROGRESS: 'in_progress'
} as const;

// Compliance thresholds
export const COMPLIANCE = {
  MISSED_SESSIONS_NUDGE_THRESHOLD: 3, // ≥3 missed in 7 days → nudge
  PLAN_COMPLETION_THRESHOLD: 0.70,   // 70% completion → prompt new plan
  NEW_PLAN_PROMPT_DAY: 25,           // Day 25 → prompt for new plan
  PLAN_DURATION_DAYS: 28             // Exactly 28 days per specification
} as const;

// Chart color schemes for progress tracking
export const CHART_COLORS = {
  PRIMARY: '#3b82f6',
  SECONDARY: '#8b5cf6', 
  SUCCESS: '#10b981',
  WARNING: '#f59e0b',
  DANGER: '#ef4444',
  INFO: '#06b6d4',
  NEUTRAL: '#6b7280'
} as const;

// Progress chart types
export const CHART_TYPES = {
  WEIGHT: 'weight_trend',
  BODY_FAT: 'body_fat_trend', 
  MUSCLE_PCT: 'muscle_percentage_trend',
  MEASUREMENTS: 'measurements_trend',
  COMPLIANCE: 'compliance_trend'
} as const;

// Error codes matching backend
export const ERROR_CODES = {
  INVALID_RANGE: 'INVALID_RANGE',
  LOW_QUALITY_IMAGE: 'low_quality_image',
  POSE_DETECTION_FAILED: 'pose_detection_failed',
  PROCESSING_FAILED: 'processing_failed',
  SAFETY_VALIDATION_FAILED: 'safety_validation_failed',
  INSUFFICIENT_DATA: 'insufficient_data'
} as const;

// Success message types
export const SUCCESS_TYPES = {
  PROFILE_CREATED: 'profile_created',
  WIZARD_DATA_STORED: 'wizard_data_stored',
  IMAGE_ANALYZED: 'image_analyzed',
  PLAN_GENERATED: 'plan_generated',
  PLAN_ACCEPTED: 'plan_accepted',
  SESSION_LOGGED: 'session_logged'
} as const;

// Legal disclaimer (always included)
export const LEGAL_DISCLAIMER = 
  "Information is for educational purposes only and is not a substitute for professional medical advice. Consult a healthcare provider before starting any exercise or nutrition program.";

// App configuration
export const APP_CONFIG = {
  API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  API_TIMEOUT: 30000, // 30 seconds
  IMAGE_UPLOAD_TIMEOUT: 60000, // 60 seconds for image processing
  RETRY_ATTEMPTS: 3,
  DEBOUNCE_DELAY: 300,
  
  // Feature flags
  ENABLE_VISION_ANALYSIS: true,
  ENABLE_SMART_SCALE_INTEGRATION: true,
  ENABLE_PROGRESS_TRACKING: true,
  ENABLE_PDF_DOWNLOAD: true,
  ENABLE_PLAN_REGENERATION: true,
  
  // Environment
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD
} as const;

// Export type definitions for TypeScript
export type FitnessGoal = keyof typeof FITNESS_GOALS;
export type ActivityLevel = keyof typeof ACTIVITY_LEVELS;
export type Sex = keyof typeof SEX_OPTIONS;
export type PostureAlert = keyof typeof POSTURE_ALERTS;
export type PlanStatus = typeof PLAN_STATUS[keyof typeof PLAN_STATUS];
export type SessionStatus = typeof SESSION_STATUS[keyof typeof SESSION_STATUS];
export type ChartType = typeof CHART_TYPES[keyof typeof CHART_TYPES];
export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

// Helper functions for unit display
export const formatMetricWeight = (kg: number, showImperial = false): string => {
  if (showImperial) {
    const lbs = kg * UNIT_CONVERSIONS.KG_TO_LBS;
    return `${kg.toFixed(1)} kg (${lbs.toFixed(1)} lbs)`;
  }
  return `${kg.toFixed(1)} kg`;
};

export const formatMetricHeight = (cm: number, showImperial = false): string => {
  if (showImperial) {
    const totalInches = cm * UNIT_CONVERSIONS.CM_TO_INCHES;
    const feet = Math.floor(totalInches / 12);
    const inches = totalInches % 12;
    return `${cm.toFixed(0)} cm (${feet}'${inches.toFixed(1)}")`;
  }
  return `${cm.toFixed(0)} cm`;
};

export const formatMetricEnergy = (kj: number, showImperial = false): string => {
  if (showImperial) {
    const kcal = kj * UNIT_CONVERSIONS.KJ_TO_KCAL;
    return `${kj.toFixed(0)} kJ (${kcal.toFixed(0)} kcal)`;
  }
  return `${kj.toFixed(0)} kJ`;
};

// Export everything as default for convenience
export default {
  APP_NAME,
  APP_VERSION,
  API_ENDPOINTS,
  FITNESS_GOALS,
  ACTIVITY_LEVELS,
  SEX_OPTIONS,
  TRAINING_DAYS,
  VALIDATION,
  CHART_COLORS,
  APP_CONFIG,
  LEGAL_DISCLAIMER
};