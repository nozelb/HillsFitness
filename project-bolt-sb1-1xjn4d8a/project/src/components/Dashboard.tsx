import React from 'react';
import { Play, Eye, Dumbbell, Target, Camera, BarChart3 } from 'lucide-react';

interface DashboardProps {
  user: any;
  onStartNewPlan: () => void;
  generatedPlan: any;
  onViewPlan: () => void;
}

function Dashboard({ user, onStartNewPlan, generatedPlan, onViewPlan }: DashboardProps) {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome back, {user.full_name}!
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Ready to optimize your fitness journey? Let's analyze your physique and create a personalized plan.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Play className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Create New Plan</h3>
            <p className="text-gray-600 mb-6">
              Upload photos, provide your data, and get an AI-generated workout and nutrition plan tailored to your goals.
            </p>
            <button
              onClick={onStartNewPlan}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Start Analysis
            </button>
          </div>
        </div>

        {generatedPlan && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Eye className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">View Your Plan</h3>
              <p className="text-gray-600 mb-6">
                Access your personalized workout and nutrition plan. Download as PDF or modify based on your progress.
              </p>
              <button
                onClick={onViewPlan}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
              >
                View Plan
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-lg p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Camera className="h-6 w-6 text-blue-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-2">1. Upload Photos</h4>
            <p className="text-sm text-gray-600">Take front and side photos for AI physique analysis</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <BarChart3 className="h-6 w-6 text-green-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-2">2. Enter Data</h4>
            <p className="text-sm text-gray-600">Provide weight, height, age, and smart scale metrics</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Target className="h-6 w-6 text-purple-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-2">3. Set Goals</h4>
            <p className="text-sm text-gray-600">Choose your fitness goal and training preferences</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Dumbbell className="h-6 w-6 text-orange-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-2">4. Get Your Plan</h4>
            <p className="text-sm text-gray-600">Receive personalized workout and nutrition guidance</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;