import React, { useState } from 'react';
import { ArrowLeft, Save, Scale } from 'lucide-react';
import ApiClient from '../api.js';

interface UserDataFormProps {
  user: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

function UserDataForm({ user, onComplete, onBack }: UserDataFormProps) {
  const [formData, setFormData] = useState({
    weight: '',
    height: '',
    age: '',
    sex: 'male',
    smart_scale: {
      body_fat_percentage: '',
      muscle_percentage: '',
      visceral_fat: ''
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSmartScaleChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      smart_scale: {
        ...prev.smart_scale,
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const userData = {
        weight: parseFloat(formData.weight),
        height: parseFloat(formData.height),
        age: parseInt(formData.age),
        sex: formData.sex,
        smart_scale: {
          body_fat_percentage: formData.smart_scale.body_fat_percentage ? 
            parseFloat(formData.smart_scale.body_fat_percentage) : null,
          muscle_percentage: formData.smart_scale.muscle_percentage ? 
            parseFloat(formData.smart_scale.muscle_percentage) : null,
          visceral_fat: formData.smart_scale.visceral_fat ? 
            parseFloat(formData.smart_scale.visceral_fat) : null,
        }
      };

      await ApiClient.storeUserData(userData, user.access_token);
      onComplete(userData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center mb-6">
          <button
            onClick={onBack}
            className="mr-4 p-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Your Physical Data</h2>
            <p className="text-gray-600 mt-1">
              Provide your measurements for accurate plan calculation
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Weight (kg) *
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.weight}
                onChange={(e) => handleInputChange('weight', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="e.g., 70.5"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Height (cm) *
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.height}
                onChange={(e) => handleInputChange('height', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="e.g., 175"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Age *
              </label>
              <input
                type="number"
                value={formData.age}
                onChange={(e) => handleInputChange('age', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="e.g., 28"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sex *
              </label>
              <select
                value={formData.sex}
                onChange={(e) => handleInputChange('sex', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                required
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>

          {/* Smart Scale Data */}
          <div className="border-t pt-6">
            <div className="flex items-center mb-4">
              <Scale className="h-5 w-5 text-blue-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">
                Smart Scale Data (Optional)
              </h3>
            </div>
            <p className="text-gray-600 mb-4 text-sm">
              If you have a smart scale, provide these metrics for more accurate calculations
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Body Fat %
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.smart_scale.body_fat_percentage}
                  onChange={(e) => handleSmartScaleChange('body_fat_percentage', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="e.g., 15.2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Muscle %
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.smart_scale.muscle_percentage}
                  onChange={(e) => handleSmartScaleChange('muscle_percentage', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="e.g., 45.8"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Visceral Fat
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.smart_scale.visceral_fat}
                  onChange={(e) => handleSmartScaleChange('visceral_fat', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="e.g., 8.5"
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save & Continue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UserDataForm;