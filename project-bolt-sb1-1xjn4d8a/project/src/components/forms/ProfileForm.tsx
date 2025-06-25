import React, { useState } from 'react';
import { Calendar, User, Target, Activity } from 'lucide-react';
import { FITNESS_GOALS, ACTIVITY_LEVELS, EXPERIENCE_LEVELS } from '../../utils/constants';
import { validateProfileForm } from '../../utils/validators';

interface ProfileFormProps {
  initialData?: any;
  onSubmit: (data: any) => void;
  onCancel?: () => void;
}

export default function ProfileForm({ initialData, onSubmit, onCancel }: ProfileFormProps) {
  const [formData, setFormData] = useState({
    fullName: initialData?.full_name || '',
    dateOfBirth: initialData?.date_of_birth || '',
    sex: initialData?.sex || '',
    primaryFitnessGoal: initialData?.primary_fitness_goal || '',
    preferredTrainingDays: initialData?.preferred_training_days || 4,
    activityLevel: initialData?.activity_level || 'moderate',
    gymExperience: initialData?.gym_experience || 'beginner',
    dietaryRestrictions: initialData?.dietary_restrictions || [],
    injuryHistory: initialData?.injury_history || []
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateProfileForm(formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    onSubmit(formData);
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Personal Information */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <User className="h-5 w-5 text-blue-600 mr-2" />
          Personal Information
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={formData.fullName}
              onChange={(e) => handleChange('fullName', e.target.value)}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.fullName ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="John Doe"
            />
            {errors.fullName && (
              <p className="text-red-500 text-xs mt-1">{errors.fullName}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date of Birth
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="date"
                value={formData.dateOfBirth}
                onChange={(e) => handleChange('dateOfBirth', e.target.value)}
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.dateOfBirth ? 'border-red-500' : 'border-gray-300'
                }`}
              />
            </div>
            {errors.dateOfBirth && (
              <p className="text-red-500 text-xs mt-1">{errors.dateOfBirth}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Biological Sex
            </label>
            <select
              value={formData.sex}
              onChange={(e) => handleChange('sex', e.target.value)}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.sex ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select...</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
            {errors.sex && (
              <p className="text-red-500 text-xs mt-1">{errors.sex}</p>
            )}
          </div>
        </div>
      </div>

      {/* Fitness Goals */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Target className="h-5 w-5 text-blue-600 mr-2" />
          Fitness Goals
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Primary Fitness Goal
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.values(FITNESS_GOALS).map(goal => (
                <button
                  key={goal.id}
                  type="button"
                  onClick={() => handleChange('primaryFitnessGoal', goal.id)}
                  className={`p-3 rounded-lg border-2 text-left transition-colors ${
                    formData.primaryFitnessGoal === goal.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">{goal.name}</div>
                  <div className="text-sm text-gray-600">{goal.description}</div>
                </button>
              ))}
            </div>
            {errors.primaryFitnessGoal && (
              <p className="text-red-500 text-xs mt-1">{errors.primaryFitnessGoal}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Training Days per Week
            </label>
            <div className="flex space-x-2">
              {[3, 4, 5, 6].map(days => (
                <button
                  key={days}
                  type="button"
                  onClick={() => handleChange('preferredTrainingDays', days)}
                  className={`px-4 py-2 rounded-lg border-2 font-medium transition-colors ${
                    formData.preferredTrainingDays === days
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {days} Days
                </button>
              ))}
            </div>
            {errors.preferredTrainingDays && (
              <p className="text-red-500 text-xs mt-1">{errors.preferredTrainingDays}</p>
            )}
          </div>
        </div>
      </div>

      {/* Activity & Experience */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Activity className="h-5 w-5 text-blue-600 mr-2" />
          Activity & Experience
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Activity Level
            </label>
            <select
              value={formData.activityLevel}
              onChange={(e) => handleChange('activityLevel', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(ACTIVITY_LEVELS).map(level => (
                <option key={level.id} value={level.id}>
                  {level.name} - {level.description}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Gym Experience
            </label>
            <select
              value={formData.gymExperience}
              onChange={(e) => handleChange('gymExperience', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(EXPERIENCE_LEVELS).map(level => (
                <option key={level.id} value={level.id}>
                  {level.name} - {level.description}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-6 border-t">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Save Profile
        </button>
      </div>
    </form>
  );
}