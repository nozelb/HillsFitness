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
  Ruler,
  Clock,
  Award,
  ChevronRight,
  PlayCircle,
  PlusCircle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import ApiClient from '../api.js';

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
}

function StatCard({ title, value, change, changeLabel, subtitle, icon: Icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600'
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {change !== null && change !== undefined && (
            <div className="flex items-center mt-2">
              {change >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {Math.abs(change).toFixed(1)}kg {changeLabel}
              </span>
            </div>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color] || colorClasses.blue}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
}

function Dashboard({ user, onStartNewPlan, generatedPlan, onViewPlan }: DashboardProps) {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showQuickLog, setShowQuickLog] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getDashboard(user.access_token);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.message);
      // Create mock data for development if API fails
      setDashboardData({
        stats: {
          current_weight: 75.0,
          weight_change_7d: -0.5,
          weight_change_30d: -2.1,
          workouts_this_week: 3,
          total_workout_time_week: 180,
          current_streak: 5,
          next_workout: {
            day: "Day 1",
            muscle_groups: ["chest", "shoulders"],
            estimated_duration_minutes: 45
          }
        },
        todays_focus: {
          workout_scheduled: {
            day: "Day 1",
            muscle_groups: ["chest", "shoulders"],
            estimated_duration_minutes: 45
          },
          nutrition_targets: {
            calories: 2200,
            protein_g: 165,
            carbs_g: 220,
            fat_g: 73
          },
          progress_logged: false,
          motivational_message: "Every workout counts! You're building a stronger you."
        },
        recent_progress: [
          { date: "2025-06-20", energy_level: 8, mood: 9, sleep_hours: 7.5 },
          { date: "2025-06-21", energy_level: 7, mood: 8, sleep_hours: 6.8 },
          { date: "2025-06-22", energy_level: 9, mood: 9, sleep_hours: 8.2 },
          { date: "2025-06-23", energy_level: 8, mood: 7, sleep_hours: 7.0 }
        ],
        weight_trend: [
          { date: "2025-06-15", weight: 77.2 },
          { date: "2025-06-18", weight: 76.8 },
          { date: "2025-06-21", weight: 75.5 },
          { date: "2025-06-24", weight: 75.0 }
        ],
        workout_frequency: [
          { week: "Week 1", workouts: 2, duration: 90 },
          { week: "Week 2", workouts: 4, duration: 200 },
          { week: "Week 3", workouts: 3, duration: 150 },
          { week: "Week 4", workouts: 3, duration: 180 }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const { stats, todays_focus, recent_progress, weight_trend, workout_frequency } = dashboardData || {};

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl text-white p-6">
        <h1 className="text-2xl font-bold mb-2">Welcome back, {user.full_name}!</h1>
        <p className="text-blue-100">{todays_focus?.motivational_message}</p>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Current Weight"
          value={stats?.current_weight ? `${stats.current_weight} kg` : 'Not set'}
          change={stats?.weight_change_7d}
          changeLabel="7d change"
          icon={Scale}
          color="blue"
        />
        <StatCard
          title="Weekly Workouts"
          value={stats?.workouts_this_week || 0}
          subtitle={`${stats?.total_workout_time_week || 0} min total`}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Current Streak"
          value={`${stats?.current_streak || 0} days`}
          icon={Award}
          color="purple"
        />
        <StatCard
          title="Next Workout"
          value={stats?.next_workout ? `${stats.next_workout.estimated_duration_minutes} min` : 'None scheduled'}
          subtitle={stats?.next_workout ? stats.next_workout.muscle_groups.join(', ') : ''}
          icon={Clock}
          color="orange"
        />
      </div>

      {/* Today's Focus */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="h-5 w-5 text-blue-600 mr-2" />
            Today's Focus
          </h3>
          
          {todays_focus?.workout_scheduled ? (
            <div className="space-y-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-blue-900">
                    {todays_focus.workout_scheduled.day}
                  </h4>
                  <PlayCircle className="h-5 w-5 text-blue-600" />
                </div>
                <p className="text-blue-700 text-sm capitalize">
                  {todays_focus.workout_scheduled.muscle_groups.join(', ')}
                </p>
                <p className="text-blue-600 text-xs mt-1">
                  {todays_focus.workout_scheduled.estimated_duration_minutes} minutes
                </p>
              </div>

              {todays_focus?.nutrition_targets && (
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-2">Nutrition Targets</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-green-600">Calories: </span>
                      <span className="font-medium">{todays_focus.nutrition_targets.calories}</span>
                    </div>
                    <div>
                      <span className="text-green-600">Protein: </span>
                      <span className="font-medium">{todays_focus.nutrition_targets.protein_g}g</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 mb-4">No workout scheduled for today</p>
              <button
                onClick={onStartNewPlan}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create New Plan
              </button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Zap className="h-5 w-5 text-purple-600 mr-2" />
            Quick Actions
          </h3>
          
          <div className="space-y-3">
            <button
              onClick={() => setShowQuickLog(!showQuickLog)}
              className="w-full flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <div className="flex items-center">
                <PlusCircle className="h-5 w-5 text-purple-600 mr-3" />
                <span className="font-medium text-purple-900">Log Progress</span>
              </div>
              <ChevronRight className="h-4 w-4 text-purple-600" />
            </button>

            <button
              onClick={onViewPlan}
              disabled={!generatedPlan}
              className="w-full flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex items-center">
                <PlayCircle className="h-5 w-5 text-green-600 mr-3" />
                <span className="font-medium text-green-900">View Current Plan</span>
              </div>
              <ChevronRight className="h-4 w-4 text-green-600" />
            </button>

            <button
              onClick={onStartNewPlan}
              className="w-full flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <div className="flex items-center">
                <Plus className="h-5 w-5 text-blue-600 mr-3" />
                <span className="font-medium text-blue-900">Generate New Plan</span>
              </div>
              <ChevronRight className="h-4 w-4 text-blue-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weight Trend Chart */}
        {weight_trend && weight_trend.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 text-blue-600 mr-2" />
              Weight Trend
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={weight_trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                    formatter={(value: any) => [`${value} kg`, 'Weight']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="weight" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Workout Frequency Chart */}
        {workout_frequency && workout_frequency.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Activity className="h-5 w-5 text-green-600 mr-2" />
              Weekly Workouts
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={workout_frequency}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: any, name: string) => [
                    name === 'workouts' ? `${value} workouts` : `${value} min`,
                    name === 'workouts' ? 'Workouts' : 'Duration'
                  ]} />
                  <Bar dataKey="workouts" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Progress Overview */}
      {recent_progress && recent_progress.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 text-purple-600 mr-2" />
            Recent Progress
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={recent_progress}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <Line 
                  type="monotone" 
                  dataKey="energy_level" 
                  stroke="#8B5CF6" 
                  strokeWidth={2}
                  name="Energy"
                />
                <Line 
                  type="monotone" 
                  dataKey="mood" 
                  stroke="#F59E0B" 
                  strokeWidth={2}
                  name="Mood"
                />
                <Line 
                  type="monotone" 
                  dataKey="sleep_hours" 
                  stroke="#06B6D4" 
                  strokeWidth={2}
                  name="Sleep Hours"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            Dashboard data unavailable. Using demo data for now.
          </p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;