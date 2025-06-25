import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity } from 'lucide-react';

interface WorkoutFrequencyProps {
  data: Array<{
    week: string;
    workouts: number;
    duration: number;
  }>;
  height?: number;
}

export default function WorkoutFrequency({ data, height = 300 }: WorkoutFrequencyProps) {
  // Calculate totals
  const totalWorkouts = data.reduce((sum, week) => sum + week.workouts, 0);
  const totalDuration = data.reduce((sum, week) => sum + week.duration, 0);
  const avgWorkoutsPerWeek = (totalWorkouts / data.length).toFixed(1);

  return (
    <div className="bg-white rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Activity className="h-5 w-5 text-green-600 mr-2" />
          Workout Frequency
        </h3>
        <div className="text-sm text-gray-600">
          Avg: {avgWorkoutsPerWeek} workouts/week
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="week" 
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
            formatter={(value: any, name: string) => [
              name === 'workouts' ? `${value} workouts` : `${value} min`,
              name === 'workouts' ? 'Workouts' : 'Total Duration'
            ]}
          />
          <Bar 
            dataKey="workouts" 
            fill="#10b981"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between text-sm">
          <div>
            <span className="text-gray-600">Total Workouts:</span>
            <span className="font-medium text-gray-900 ml-2">{totalWorkouts}</span>
          </div>
          <div>
            <span className="text-gray-600">Total Duration:</span>
            <span className="font-medium text-gray-900 ml-2">{totalDuration} min</span>
          </div>
        </div>
      </div>
    </div>
  );
}