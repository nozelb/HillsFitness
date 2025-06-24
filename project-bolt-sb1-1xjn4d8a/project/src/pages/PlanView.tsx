import React from 'react';
import { ArrowLeft, Download, RotateCcw, Dumbbell, Utensils, Clock, Target } from 'lucide-react';

interface PlanViewProps {
  plan: any;
  onBack: () => void;
  onGenerateNew: () => void;
}

function PlanView({ plan, onBack, onGenerateNew }: PlanViewProps) {
  const { workout_plan, nutrition_plan } = plan;

  const handleDownloadPDF = () => {
    // In a real app, this would generate and download a PDF
    alert('PDF download functionality would be implemented here using libraries like jsPDF or react-pdf');
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <button
              onClick={onBack}
              className="mr-4 p-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Your Personalized Plan</h2>
              <p className="text-gray-600 mt-1">
                Evidence-based workout and nutrition plan tailored to your goals
              </p>
            </div>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleDownloadPDF}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Download PDF
            </button>
            <button
              onClick={onGenerateNew}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Generate New
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Workout Plan */}
          <div className="space-y-6">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <Dumbbell className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Workout Plan</h3>
            </div>

            <div className="space-y-4">
              {workout_plan.map((day, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-gray-900">{day.day}</h4>
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock className="h-4 w-4 mr-1" />
                      {day.estimated_duration_minutes} min
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <div className="flex flex-wrap gap-2">
                      {day.muscle_groups.map((muscle, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                        >
                          {muscle}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    {day.exercises.map((exercise, idx) => (
                      <div key={idx} className="bg-white rounded p-3">
                        <div className="flex justify-between items-start mb-1">
                          <h5 className="font-medium text-gray-900">{exercise.name}</h5>
                          <span className="text-sm text-gray-600">
                            {exercise.sets} × {exercise.reps}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">
                          Rest: {exercise.rest_seconds}s
                        </p>
                        {exercise.notes && (
                          <p className="text-xs text-blue-600 mt-1">{exercise.notes}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Nutrition Plan */}
          <div className="space-y-6">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <Utensils className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Nutrition Plan</h3>
            </div>

            {/* Daily Targets */}
            <div className="bg-green-50 rounded-lg p-6">
              <h4 className="font-semibold text-green-900 mb-4 flex items-center">
                <Target className="h-5 w-5 mr-2" />
                Daily Targets
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-900">
                    {nutrition_plan.daily_targets.calories}
                  </div>
                  <div className="text-green-700 text-sm">Calories</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-900">
                    {nutrition_plan.daily_targets.protein_g}g
                  </div>
                  <div className="text-green-700 text-sm">Protein</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-900">
                    {nutrition_plan.daily_targets.carbs_g}g
                  </div>
                  <div className="text-green-700 text-sm">Carbs</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-900">
                    {nutrition_plan.daily_targets.fat_g}g
                  </div>
                  <div className="text-green-700 text-sm">Fat</div>
                </div>
              </div>
            </div>

            {/* Metabolic Info */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-3">Metabolic Information</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">BMR (Basal Metabolic Rate):</span>
                  <span className="font-medium">{nutrition_plan.bmr} cal/day</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">TDEE (Total Daily Energy):</span>
                  <span className="font-medium">{nutrition_plan.tdee} cal/day</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Hydration Target:</span>
                  <span className="font-medium">{nutrition_plan.hydration_target_ml}ml/day</span>
                </div>
              </div>
            </div>

            {/* Sample Meals */}
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Sample Meal Plan</h4>
              {nutrition_plan.meal_suggestions.map((meal, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h5 className="font-medium text-gray-900 capitalize">{meal.meal_type}</h5>
                    <span className="text-sm text-gray-600">{meal.calories} cal</span>
                  </div>
                  <p className="text-sm font-medium text-gray-800 mb-2">{meal.name}</p>
                  <div className="text-xs text-gray-600 mb-2">
                    P: {meal.protein_g}g | C: {meal.carbs_g}g | F: {meal.fat_g}g
                  </div>
                  <div className="text-xs text-gray-600">
                    <strong>Ingredients:</strong> {meal.ingredients.join(', ')}
                  </div>
                </div>
              ))}
            </div>

            {/* Notes */}
            {nutrition_plan.notes && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Important Notes</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  {nutrition_plan.notes.map((note, index) => (
                    <li key={index}>• {note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Rationale */}
        {plan.rationale && (
          <div className="mt-8 bg-yellow-50 rounded-lg p-6">
            <h4 className="font-semibold text-yellow-900 mb-2">Plan Rationale</h4>
            <p className="text-yellow-800 text-sm">{plan.rationale}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PlanView;