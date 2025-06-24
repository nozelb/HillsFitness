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
  ChevronRight
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import ApiClient from '../api.js';

interface DashboardProps {
  user: any;
  onNavigate: (page: string) => void;
}

function Dashboard({ user, onNavigate }: DashboardProps) {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Failed to load dashboard: {error}</p>
        <button 
          onClick={loadDashboardData}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
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