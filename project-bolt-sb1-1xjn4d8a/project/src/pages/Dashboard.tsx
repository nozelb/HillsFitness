import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Calendar, 
  Zap, 
  Plus,
  Activity,
  Scale,
  Clock,
  Award,
  ChevronRight,
  PlayCircle,
  PlusCircle,
  Dumbbell,
  AlertCircle,
  Users,
  Timer
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import ApiClient from '../api';

interface DashboardProps {
  user: any;
  onStartNewPlan: () => void;
  generatedPlan: any;
  onViewPlan: () => void;
}

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null;
  changeLabel?: string;
  subtitle?: string;
  icon: React.ComponentType<any>;
  color: string;
  isEmpty?: boolean;
}

interface TodaysWorkoutModalProps {
  workout: any;
  isOpen: boolean;
  onClose: () => void;
  onStartWorkout: () => void;
}

function TodaysWorkoutModal({ workout, isOpen, onClose, onStartWorkout }: TodaysWorkoutModalProps) {
  if (!isOpen || !workout) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Today's Workout</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              ✕
            </button>
          </div>

          <div className="mb-6">
            <div className="bg-blue-50 rounded-lg p-4 mb-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">{workout.day}</h3>
              <div className="flex items-center space-x-4 text-sm text-blue-700">
                <div className="flex items-center">
                  <Users className="h-4 w-4 mr-1" />
                  <span>{workout.muscle_groups.join(', ').toUpperCase()}</span>
                </div>
                <div className="flex items-center">
                  <Timer className="h-4 w-4 mr-1" />
                  <span>{workout.estimated_duration_minutes} minutes</span>
                </div>
                <div className="flex items-center">
                  <Activity className="h-4 w-4 mr-1" />
                  <span>Week {workout.week_number || 1}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4 mb-6">
            <h4 className="font-semibold text-gray-900">Exercises ({workout.exercises?.length || 0})</h4>
            {workout.exercises?.map((exercise: any, index: number) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h5 className="font-medium text-gray-900">{exercise.name}</h5>
                  <span className="text-sm text-gray-600 bg-white px-2 py-1 rounded">
                    {exercise.sets} × {exercise.reps}
                  </span>
                </div>
                {exercise.target_muscle && (
                  <p className="text-xs text-blue-600 mb-1">Target: {exercise.target_muscle}</p>
                )}
                <div className="flex justify-between items-center text-sm text-gray-600">
                  <span>Rest: {exercise.rest_seconds}s</span>
                  {exercise.equipment && (
                    <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">
                      {exercise.equipment}
                    </span>
                  )}
                </div>
                {exercise.notes && (
                  <p className="text-xs text-gray-500 mt-2 italic">{exercise.notes}</p>
                )}
              </div>
            ))}
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onStartWorkout}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
            >
              <PlayCircle className="h-5 w-5" />
              <span>Start Workout</span>
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, change, changeLabel, subtitle, icon: Icon, color, isEmpty }: StatCardProps) {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600',
      green: 'bg-green-50 text-green-600',
      red: 'bg-red-50 text-red-600',
      purple: 'bg-purple-50 text-purple-600',
      yellow: 'bg-yellow-50 text-yellow-600',
      gray: 'bg-gray-50 text-gray-600'
    };
    return colors[color as keyof typeof colors] || colors.gray;
  };

  if (isEmpty) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-400">--</p>
            <p className="text-sm text-gray-400">No data yet</p>
          </div>
          <div className={`w-12 h-12 rounded-full ${getColorClasses(color)} flex items-center justify-center opacity-50`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change !== null && change !== undefined && (
            <div className="flex items-center space-x-1">
              {change > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : change < 0 ? (
                <TrendingDown className="h-4 w-4 text-red-500" />
              ) : null}
              <span className={`text-sm ${change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {change > 0 ? '+' : ''}{change.toFixed(1)}kg {changeLabel}
              </span>
            </div>
          )}
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 rounded-full ${getColorClasses(color)} flex items-center justify-center`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
}

function Dashboard({ user, onStartNewPlan, generatedPlan, onViewPlan }: DashboardProps) {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWorkoutModal, setShowWorkoutModal] = useState(false);
  const [todaysWorkout, setTodaysWorkout] = useState<any>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await ApiClient.get('/api/dashboard');
      setDashboardData(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Dashboard fetch error:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTodaysWorkout = async () => {
    try {
      const response = await ApiClient.get('/api/todays-workout');
      setTodaysWorkout(response.data);
    } catch (err) {
      console.error('Failed to fetch today\'s workout:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchTodaysWorkout();
  }, []);

  const handleTodaysFocusClick = () => {
    if (todaysWorkout?.workout) {
      setShowWorkoutModal(true);
    }
  };

  const handleStartWorkout = () => {
    setShowWorkoutModal(false);
    // Here you would typically navigate to a workout tracking page
    alert('Workout tracking feature coming soon!');
  };

  const handleLogProgress = () => {
    // Here you would open a progress logging modal
    alert('Progress logging feature coming soon!');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to load dashboard</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No dashboard data available</p>
      </div>
    );
  }

  const { stats, todays_focus, recent_progress, weight_trend, workout_frequency, has_active_plan, data_available } = dashboardData;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.full_name?.split(' ')[0] || 'Athlete'}!
        </h1>
        <p className="text-gray-600">
          {has_active_plan 
            ? "Keep up the great work with your fitness journey" 
            : "Ready to start your personalized fitness journey?"
          }
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Current Weight"
          value={stats.current_weight ? `${stats.current_weight}kg` : '--'}
          change={stats.weight_change_7d}
          changeLabel="this week"
          icon={Scale}
          color="blue"
          isEmpty={!stats.current_weight}
        />
        <StatCard
          title="Workouts This Week"
          value={stats.workouts_this_week}
          subtitle={`${stats.total_workout_time_week} minutes total`}
          icon={Activity}
          color="green"
          isEmpty={!data_available.workout_logs}
        />
        <StatCard
          title="Current Streak"
          value={`${stats.current_streak} days`}
          subtitle="Keep it up!"
          icon={Award}
          color="purple"
          isEmpty={!data_available.workout_logs}
        />
        <StatCard
          title="Weight Change"
          value={stats.weight_change_30d ? `${stats.weight_change_30d > 0 ? '+' : ''}${stats.weight_change_30d.toFixed(1)}kg` : '--'}
          subtitle="30 days"
          icon={TrendingUp}
          color={stats.weight_change_30d > 0 ? 'red' : stats.weight_change_30d < 0 ? 'green' : 'gray'}
          isEmpty={!data_available.weight_logs}
        />
      </div>

      {/* Today's Focus */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Today's Focus</h2>
        
        {!has_active_plan ? (
          <div className="text-center py-8">
            <Target className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active Plan</h3>
            <p className="text-gray-600 mb-4">Generate your personalized AI workout and nutrition plan to get started</p>
            <button
              onClick={onStartNewPlan}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
            >
              <PlusCircle className="h-5 w-5" />
              <span>Create Your Plan</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Workout Widget */}
            <div 
              className={`bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 cursor-pointer transition-all duration-200 hover:from-blue-100 hover:to-blue-200 hover:shadow-md ${
                todaysWorkout?.workout ? 'hover:scale-[1.02]' : 'opacity-75'
              }`}
              onClick={handleTodaysFocusClick}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-blue-900">Today's Workout</h3>
                {todaysWorkout?.workout && <ChevronRight className="h-5 w-5 text-blue-600" />}
              </div>
              {todaysWorkout?.workout ? (
                <div>
                  <p className="text-blue-800 font-medium">{todaysWorkout.workout.day}</p>
                  <p className="text-sm text-blue-600">{todaysWorkout.workout.muscle_groups.join(', ')}</p>
                  <p className="text-sm text-blue-600">{todaysWorkout.workout.estimated_duration_minutes} minutes</p>
                  <div className="mt-2 text-xs text-blue-700">
                    Click to view exercises →
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-blue-800">No workout scheduled</p>
                  <p className="text-sm text-blue-600">Rest day or plan needed</p>
                </div>
              )}
            </div>

            {/* Nutrition Widget */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">Nutrition Targets</h3>
              {todays_focus.nutrition_targets ? (
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">Calories:</span>
                    <span className="text-sm font-medium text-green-800">{todays_focus.nutrition_targets.calories}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">Protein:</span>
                    <span className="text-sm font-medium text-green-800">{todays_focus.nutrition_targets.protein_g}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">Carbs:</span>
                    <span className="text-sm font-medium text-green-800">{todays_focus.nutrition_targets.carbs_g}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">Fat:</span>
                    <span className="text-sm font-medium text-green-800">{todays_focus.nutrition_targets.fat_g}g</span>
                  </div>
                </div>
              ) : (
                <p className="text-green-700">No nutrition plan active</p>
              )}
            </div>

            {/* Progress Widget */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-purple-900">Daily Progress</h3>
                <button
                  onClick={handleLogProgress}
                  className="text-purple-600 hover:text-purple-700 transition-colors"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              {todays_focus.progress_logged ? (
                <div className="flex items-center text-green-700">
                  <Zap className="h-4 w-4 mr-1" />
                  <span className="text-sm">Progress logged today!</span>
                </div>
              ) : (
                <div className="text-purple-700">
                  <p className="text-sm">Log your energy, mood, and sleep</p>
                  <p className="text-xs text-purple-600 mt-1">Track your daily metrics</p>
                </div>
              )}
              <div className="mt-2">
                <p className="text-xs text-purple-600 italic">{todays_focus.motivational_message}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Charts Section */}
      {(data_available.weight_logs || data_available.workout_logs || data_available.progress_entries) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weight Trend Chart */}
          {data_available.weight_logs && weight_trend.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Weight Trend</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={weight_trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="weight" stroke="#3B82F6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Workout Frequency Chart */}
          {data_available.workout_logs && workout_frequency.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Workout Frequency</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={workout_frequency}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="workouts" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Progress Chart */}
          {data_available.progress_entries && recent_progress.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 lg:col-span-2">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Progress</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={recent_progress}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="energy_level" stroke="#F59E0B" strokeWidth={2} name="Energy" />
                  <Line type="monotone" dataKey="mood" stroke="#8B5CF6" strokeWidth={2} name="Mood" />
                  <Line type="monotone" dataKey="sleep_hours" stroke="#06B6D4" strokeWidth={2} name="Sleep Hours" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Empty State for Charts */}
      {!data_available.weight_logs && !data_available.workout_logs && !data_available.progress_entries && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <div className="max-w-sm mx-auto">
            <div className="bg-gray-100 rounded-full p-3 w-16 h-16 mx-auto mb-4">
              <Activity className="h-10 w-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Start Tracking Your Progress</h3>
            <p className="text-gray-600 mb-4">
              Log your workouts, weight, and daily progress to see your fitness journey visualized with charts and trends.
            </p>
            <div className="space-y-2">
              <button
                onClick={handleLogProgress}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Log Today's Progress
              </button>
              {generatedPlan && (
                <button
                  onClick={onViewPlan}
                  className="w-full border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  View My Plan
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Today's Workout Modal */}
      <TodaysWorkoutModal
        workout={todaysWorkout?.workout}
        isOpen={showWorkoutModal}
        onClose={() => setShowWorkoutModal(false)}
        onStartWorkout={handleStartWorkout}
      />
    </div>
  );
}

export default Dashboard;