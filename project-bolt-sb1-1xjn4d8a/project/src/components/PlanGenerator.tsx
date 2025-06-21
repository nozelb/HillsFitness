import React, { useState } from 'react';
import { ArrowLeft, Target, Calendar, Activity, Zap } from 'lucide-react';
import ApiClient from '../api.js';

interface PlanGeneratorProps {
  user: any;
  imageAnalysis: any;
  userData: any;
  onComplete: (plan: any) => void;
  onBack: () => void;
}

function PlanGenerator({ user, imageAnalysis, userData, onComplete, onBack }: PlanGeneratorProps) {
  const [fitnessGoal, setFitnessGoal] = useState('');
  const [daysPerWeek, setDaysPerWeek] = useState(4);
  const [activityLevel, setActivityLevel] = useState('moderate');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const goals = [
    {
      id: 'lose_fat',
      name: 'Lose Fat',
      description: 'Reduce body fat while maintaining muscle',
      icon: Target,
      color: 'red'
    },
    {
      id: 'gain_muscle',
      name: 'Build Muscle',
      description: 'Increase muscle mass and strength',
      icon: Zap,
      color: 'blue'
    },
    {
      id: 'recomposition',
      name: 'Body Recomposition',
      description: 'Build muscle while losing fat',
      icon: Activity,
      color: 'purple'
    },
    {
      id: 'maintenance',
      name: 'Maintain',
      description: 'Maintain current physique and health',
      icon: Calendar,
      color: 'green'
    }
  ];

  const activityLevels = [
    { id: 'sedentary', name: 'Sedentary', description: 'Little to no exercise' },
    { id: 'light', name: 'Light', description: 'Light exercise 1-3 days/week' },
    { id: 'moderate', name: 'Moderate', description: 'Moderate exercise 3-5 days/week' },
    { id: 'active', name: 'Active', description: 'Heavy exercise 6-7 days/week' },
    { id: 'very_active', name: 'Very Active', description: 'Very heavy exercise or physical job' }
  ];

  const handleGeneratePlan = async () => {
    if (!fitnessGoal) {
      setError('Please select a fitness goal');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const planRequest = {
        fitness_goal: fitnessGoal,
        days_per_week: daysPerWeek,
        activity_level: activityLevel
      };

      const plan = await ApiClient.generatePlan(planRequest, user.access_token);
      onComplete(plan);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center mb-6">
          <button
            onClick={onBack}
            className="mr-4 p-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Set Your Goals</h2>
            <p className="text-gray-600 mt-1">
              Choose your fitness goal and preferences to generate your personalized plan
            </p>
          </div>
        </div>

        <div className="space-y-8">
          {/* Fitness Goals */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">What's your primary fitness goal?</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {goals.map((goal) => {
                const Icon = goal.icon;
                const isSelected = fitnessGoal === goal.id;
                return (
                  <button
                    key={goal.id}
                    onClick={() => setFitnessGoal(goal.id)}
                    className={`
                      p-6 rounded-lg border-2 text-left transition-all
                      ${isSelected 
                        ? `border-${goal.color}-500 bg-${goal.color}-50` 
                        : 'border-gray-200 hover:border-gray-300'
                      }
                    `}
                  >
                    <div className="flex items-start">
                      <div className={`
                        w-12 h-12 rounded-lg flex items-center justify-center mr-4
                        ${isSelected 
                          ? `bg-${goal.color}-100` 
                          : 'bg-gray-100'
                        }
                      `}>
                        <Icon className={`h-6 w-6 ${isSelected ? `text-${goal.color}-600` : 'text-gray-600'}`} />
                      </div>
                      <div>
                        <h4 className={`font-medium ${isSelected ? `text-${goal.color}-900` : 'text-gray-900'}`}>
                          {goal.name}
                        </h4>
                        <p className={`text-sm mt-1 ${isSelected ? `text-${goal.color}-700` : 'text-gray-600'}`}>
                          {goal.description}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Training Frequency */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">How many days per week can you train?</h3>
            <div className="flex space-x-4">
              {[3, 4, 5].map((days) => (
                <button
                  key={days}
                  onClick={() => setDaysPerWeek(days)}
                  className={`
                    px-6 py-3 rounded-lg border-2 font-medium transition-all
                    ${daysPerWeek === days 
                      ? 'border-blue-500 bg-blue-50 text-blue-700' 
                      : 'border-gray-200 text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {days} Days
                </button>
              ))}
            </div>
          </div>

          {/* Activity Level */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">What's your current activity level?</h3>
            <div className="space-y-3">
              {activityLevels.map((level) => (
                <button
                  key={level.id}
                  onClick={() => setActivityLevel(level.id)}
                  className={`
                    w-full p-4 rounded-lg border-2 text-left transition-all
                    ${activityLevel === level.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                    }
                  `}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className={`font-medium ${activityLevel === level.id ? 'text-blue-900' : 'text-gray-900'}`}>
                        {level.name}
                      </h4>
                      <p className={`text-sm ${activityLevel === level.id ? 'text-blue-700' : 'text-gray-600'}`}>
                        {level.description}
                      </p>
                    </div>
                    <div className={`
                      w-5 h-5 rounded-full border-2
                      ${activityLevel === level.id 
                        ? 'border-blue-500 bg-blue-500' 
                        : 'border-gray-300'
                      }
                    `}>
                      {activityLevel === level.id && (
                        <div className="w-full h-full rounded-full bg-white transform scale-50"></div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleGeneratePlan}
              disabled={loading || !fitnessGoal}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Generating Plan...
                </>
              ) : (
                <>
                  <Target className="h-5 w-5 mr-2" />
                  Generate My Plan
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlanGenerator;