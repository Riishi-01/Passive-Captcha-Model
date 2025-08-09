import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const mockData = [
  { time: '00:00', accuracy: 94.2 },
  { time: '04:00', accuracy: 95.1 },
  { time: '08:00', accuracy: 93.8 },
  { time: '12:00', accuracy: 96.3 },
  { time: '16:00', accuracy: 94.9 },
  { time: '20:00', accuracy: 95.7 },
  { time: '24:00', accuracy: 95.2 },
]

export default function ModelAccuracyChart({ data = mockData }) {
  return (
    <div className="card p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Model Accuracy Trend
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Last 24 hours
        </p>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis 
              dataKey="time" 
              tick={{ fill: 'currentColor', fontSize: 12 }}
              className="text-gray-600 dark:text-gray-400"
            />
            <YAxis 
              domain={['dataMin - 1', 'dataMax + 1']}
              tick={{ fill: 'currentColor', fontSize: 12 }}
              className="text-gray-600 dark:text-gray-400"
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'var(--tw-colors-white)',
                border: '1px solid var(--tw-colors-gray-200)',
                borderRadius: '0.5rem',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="accuracy" 
              stroke="#2563eb" 
              strokeWidth={2}
              dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#2563eb', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
