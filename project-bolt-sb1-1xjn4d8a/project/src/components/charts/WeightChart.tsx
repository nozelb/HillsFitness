import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface WeightChartProps {
  data: Array<{
    date: string;
    weight: number;
    body_fat?: number;
  }>;
  height?: number;
}

export default function WeightChart({ data, height = 300 }: WeightChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg p-4 h-full flex items-center justify-center">
        <p className="text-gray-500">No weight data available</p>
      </div>
    );
  }

  // Calculate weight change
  const firstWeight = data[0].weight;
  const lastWeight = data[data.length - 1].weight;
  const weightChange = lastWeight - firstWeight;
  const percentChange = ((weightChange / firstWeight) * 100).toFixed(1);

  // Format data for display
  const formattedData = data.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }));

  return (
    <div className="bg-white rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Weight Trend</h3>
        <div className="flex items-center space-x-2">
          {weightChange >= 0 ? (
            <TrendingUp className="h-5 w-5 text-green-500" />
          ) : (
            <TrendingDown className="h-5 w-5 text-red-500" />
          )}
          <span className={`text-sm font-medium ${weightChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {weightChange >= 0 ? '+' : ''}{weightChange.toFixed(1)} kg ({percentChange}%)
          </span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={formattedData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
            formatter={(value: any, name: string) => [
              `${value} ${name === 'weight' ? 'kg' : '%'}`,
              name === 'weight' ? 'Weight' : 'Body Fat'
            ]}
          />
          <Line 
            type="monotone" 
            dataKey="weight" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          {data.some(d => d.body_fat) && (
            <Line 
              type="monotone" 
              dataKey="body_fat" 
              stroke="#ef4444" 
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: '#ef4444', r: 3 }}
              yAxisId="right"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}