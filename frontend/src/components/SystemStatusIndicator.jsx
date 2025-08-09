import { CheckCircle, AlertCircle, XCircle } from 'lucide-react'

export default function SystemStatusIndicator({ status, message }) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400'
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'error':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy':
        return CheckCircle
      case 'warning':
        return AlertCircle
      case 'error':
        return XCircle
      default:
        return AlertCircle
    }
  }

  const StatusIcon = getStatusIcon()

  return (
    <div className="flex items-center space-x-2">
      <StatusIcon className={`h-5 w-5 ${getStatusColor()}`} />
      <span className={`text-sm font-medium ${getStatusColor()}`}>
        {message || status}
      </span>
    </div>
  )
}
