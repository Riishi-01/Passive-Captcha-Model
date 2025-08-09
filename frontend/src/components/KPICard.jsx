import { TrendingUp, TrendingDown } from 'lucide-react'

export default function KPICard({ title, value, change, icon: Icon, trend }) {
  const isPositive = trend === 'up' || (change && change > 0)
  const isNegative = trend === 'down' || (change && change < 0)

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {value}
          </p>
          {change !== undefined && (
            <div className={`flex items-center mt-1 text-sm ${
              isPositive 
                ? 'text-green-600 dark:text-green-400' 
                : isNegative 
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-600 dark:text-gray-400'
            }`}>
              {isPositive && <TrendingUp className="h-4 w-4 mr-1" />}
              {isNegative && <TrendingDown className="h-4 w-4 mr-1" />}
              {Math.abs(change)}% from last period
            </div>
          )}
        </div>
        {Icon && (
          <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-full">
            <Icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
        )}
      </div>
    </div>
  )
}
