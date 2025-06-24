import React, { useState, useEffect } from 'react';
import { User, Dumbbell, Target, Camera, BarChart3 } from 'lucide-react';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './pages/Dashboard';
import ImageUpload from './components/ImageUpload';
import UserDataForm from './components/UserDataForm';
import PlanGenerator from './pages/PlanGenerator';
import PlanView from './pages/PlanView';

interface User {
  id: string;
  email: string;
  full_name: string;
  access_token: string;
}

interface Plan {
  id: string;
  workout_plan: any[];
  nutrition_plan: any;
  rationale: string;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [currentStep, setCurrentStep] = useState('dashboard');
  const [showLogin, setShowLogin] = useState(true);
  const [generatedPlan, setGeneratedPlan] = useState<Plan | null>(null);
  const [imageAnalysis, setImageAnalysis] = useState(null);
  const [userData, setUserData] = useState(null);

  useEffect(() => {
    // Check for stored user data
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    setCurrentStep('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    setCurrentStep('dashboard');
    setGeneratedPlan(null);
    setImageAnalysis(null);
    setUserData(null);
  };

  const handleStepComplete = (step: string, data?: any) => {
    if (step === 'image') {
      setImageAnalysis(data);
      setCurrentStep('userdata');
    } else if (step === 'userdata') {
      setUserData(data);
      setCurrentStep('generate');
    } else if (step === 'generate') {
      setGeneratedPlan(data);
      setCurrentStep('plan');
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'dashboard', name: 'Start', icon: User, completed: true },
      { id: 'image', name: 'Photo', icon: Camera, completed: imageAnalysis !== null },
      { id: 'userdata', name: 'Data', icon: BarChart3, completed: userData !== null },
      { id: 'generate', name: 'Goals', icon: Target, completed: false },
      { id: 'plan', name: 'Plan', icon: Dumbbell, completed: generatedPlan !== null },
    ];

    return (
      <div className="flex justify-center mb-8">
        <div className="flex items-center space-x-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = step.completed;
            
            return (
              <div key={step.id} className="flex items-center">
                <div
                  className={`
                    flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all
                    ${isActive 
                      ? 'bg-blue-600 border-blue-600 text-white' 
                      : isCompleted 
                        ? 'bg-green-500 border-green-500 text-white'
                        : 'bg-gray-200 border-gray-300 text-gray-500'
                    }
                  `}
                >
                  <Icon size={16} />
                </div>
                <span className={`ml-2 text-sm font-medium ${isActive ? 'text-blue-600' : 'text-gray-500'}`}>
                  {step.name}
                </span>
                {index < steps.length - 1 && (
                  <div className={`w-8 h-0.5 ml-4 ${isCompleted ? 'bg-green-500' : 'bg-gray-300'}`} />
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-6">
              <Dumbbell className="h-12 w-12 text-blue-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">Gym AI Coach</h1>
            </div>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Get personalized workout and nutrition plans powered by AI analysis of your physique
            </p>
          </div>

          <div className="max-w-md mx-auto">
            {showLogin ? (
              <Login 
                onLogin={handleLogin} 
                onSwitchToRegister={() => setShowLogin(false)} 
              />
            ) : (
              <Register 
                onRegister={handleLogin} 
                onSwitchToLogin={() => setShowLogin(true)} 
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Dumbbell className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Gym AI Coach</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Hello, {user.full_name}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {user && renderStepIndicator()}

        <div className="max-w-4xl mx-auto">
          {currentStep === 'dashboard' && (
            <Dashboard 
              user={user} 
              onStartNewPlan={() => setCurrentStep('image')}
              generatedPlan={generatedPlan}
              onViewPlan={() => setCurrentStep('plan')}
            />
          )}
          
          {currentStep === 'image' && (
            <ImageUpload 
              user={user} 
              onComplete={(data) => handleStepComplete('image', data)}
              onBack={() => setCurrentStep('dashboard')}
            />
          )}
          
          {currentStep === 'userdata' && (
            <UserDataForm 
              user={user} 
              onComplete={(data) => handleStepComplete('userdata', data)}
              onBack={() => setCurrentStep('image')}
            />
          )}
          
          {currentStep === 'generate' && (
            <PlanGenerator 
              user={user} 
              imageAnalysis={imageAnalysis}
              userData={userData}
              onComplete={(data) => handleStepComplete('generate', data)}
              onBack={() => setCurrentStep('userdata')}
            />
          )}
          
          {currentStep === 'plan' && generatedPlan && (
            <PlanView 
              plan={generatedPlan}
              onBack={() => setCurrentStep('dashboard')}
              onGenerateNew={() => setCurrentStep('image')}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;