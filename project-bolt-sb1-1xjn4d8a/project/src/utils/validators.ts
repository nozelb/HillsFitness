import { VALIDATION } from './constants';

// Email validation
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Password validation
export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (password.length < VALIDATION.MIN_PASSWORD_LENGTH) {
    errors.push(`Password must be at least ${VALIDATION.MIN_PASSWORD_LENGTH} characters`);
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Age validation
export const isValidAge = (dateOfBirth: Date): boolean => {
  const today = new Date();
  const birthDate = new Date(dateOfBirth);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  
  return age >= VALIDATION.MIN_AGE && age <= VALIDATION.MAX_AGE;
};

// Measurement validations
export const isValidHeight = (height: number): boolean => {
  return height >= VALIDATION.MIN_HEIGHT_CM && height <= VALIDATION.MAX_HEIGHT_CM;
};

export const isValidWeight = (weight: number): boolean => {
  return weight >= VALIDATION.MIN_WEIGHT_KG && weight <= VALIDATION.MAX_WEIGHT_KG;
};

export const isValidBodyFat = (bodyFat: number): boolean => {
  return bodyFat >= VALIDATION.MIN_BODY_FAT && bodyFat <= VALIDATION.MAX_BODY_FAT;
};

// File validation
export const isValidImageFile = (file: File): { isValid: boolean; error?: string } => {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  const maxSize = VALIDATION.MAX_FILE_SIZE_MB * 1024 * 1024; // Convert to bytes
  
  if (!validTypes.includes(file.type)) {
    return { isValid: false, error: 'File must be JPEG or PNG' };
  }
  
  if (file.size > maxSize) {
    return { isValid: false, error: `File size must be less than ${VALIDATION.MAX_FILE_SIZE_MB}MB` };
  }
  
  return { isValid: true };
};

// Form validation helpers
export const validateMeasurements = (measurements: any): { [key: string]: string } => {
  const errors: { [key: string]: string } = {};
  
  if (!measurements.height || !isValidHeight(measurements.height)) {
    errors.height = `Height must be between ${VALIDATION.MIN_HEIGHT_CM}-${VALIDATION.MAX_HEIGHT_CM} cm`;
  }
  
  if (!measurements.weight || !isValidWeight(measurements.weight)) {
    errors.weight = `Weight must be between ${VALIDATION.MIN_WEIGHT_KG}-${VALIDATION.MAX_WEIGHT_KG} kg`;
  }
  
  if (measurements.bodyFat && !isValidBodyFat(measurements.bodyFat)) {
    errors.bodyFat = `Body fat must be between ${VALIDATION.MIN_BODY_FAT}-${VALIDATION.MAX_BODY_FAT}%`;
  }
  
  return errors;
};

export const validateProfileForm = (profile: any): { [key: string]: string } => {
  const errors: { [key: string]: string } = {};
  
  if (!profile.fullName || profile.fullName.trim().length < 2) {
    errors.fullName = 'Full name is required';
  }
  
  if (!profile.dateOfBirth) {
    errors.dateOfBirth = 'Date of birth is required';
  } else if (!isValidAge(new Date(profile.dateOfBirth))) {
    errors.dateOfBirth = `Age must be between ${VALIDATION.MIN_AGE}-${VALIDATION.MAX_AGE} years`;
  }
  
  if (!profile.sex || !['male', 'female'].includes(profile.sex)) {
    errors.sex = 'Please select your biological sex';
  }
  
  if (!profile.primaryFitnessGoal) {
    errors.primaryFitnessGoal = 'Please select a fitness goal';
  }
  
  if (!profile.preferredTrainingDays || 
      profile.preferredTrainingDays < VALIDATION.MIN_TRAINING_DAYS || 
      profile.preferredTrainingDays > VALIDATION.MAX_TRAINING_DAYS) {
    errors.preferredTrainingDays = `Training days must be between ${VALIDATION.MIN_TRAINING_DAYS}-${VALIDATION.MAX_TRAINING_DAYS}`;
  }
  
  if (!profile.activityLevel) {
    errors.activityLevel = 'Please select your activity level';
  }
  
  if (!profile.gymExperience) {
    errors.gymExperience = 'Please select your experience level';
  }
  
  return errors;
};

// Sanitization helpers
export const sanitizeInput = (input: string): string => {
  return input.trim().replace(/<[^>]*>/g, '');
};

export const sanitizeNumber = (input: any): number | null => {
  const num = parseFloat(input);
  return isNaN(num) ? null : num;
};