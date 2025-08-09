import { useEffect, useState } from 'react'
import { Clock, Globe, Shield, AlertTriangle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function LiveActivityFeed() {
  const [activities, setActivities] = useState([])

  useEffect(() => {
    // Mock data - replace with real API call
    const mockActivities = [
      {
        id: 1,
        type: 'verification',
        message: 'New verification request from example.com',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        icon: Shield,
        color: 'text-green-600'
      },
      {
        id: 2,
        type: 'website',
        message: 'Website "demo.site" added to monitoring',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        icon: Globe,
        color: 'text-blue-600'
      },
      {
        id: 3,
        type: 'alert',
        message: 'High confidence threshold alert triggered',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        icon: AlertTriangle,
        color: 'text-yellow-600'
      },
      {
        id: 4,
        type: 'verification',
        message: 'Bot detected and blocked on shop.example',
        timestamp: new Date(Date.now() - 45 * 60 * 1000),
        icon: Shield,
        color: 'text-red-600'
      },
    ]
    setActivities(mockActivities)
  }, [])

  return (
    <div className="card">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Live Activity
        </h3>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {activities.map((activity) => (
          <div key={activity.id} className="px-6 py-4 flex items-start space-x-3">
            <div className={`flex-shrink-0 ${activity.color}`}>
              <activity.icon className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900 dark:text-white">
                {activity.message}
              </p>
              <div className="mt-1 flex items-center text-xs text-gray-500 dark:text-gray-400">
                <Clock className="h-3 w-3 mr-1" />
                {formatDistanceToNow(activity.timestamp, { addSuffix: true })}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800">
        <a href="/dashboard/logs" className="text-sm text-primary-600 hover:text-primary-500">
          View all activity →
        </a>
      </div>
    </div>
  )
}
