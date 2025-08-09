import { useState, useEffect } from 'react'
import { Clock } from 'lucide-react'

export default function RealTimeClock() {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Format time for IST (UTC +5:30)
  const formatISTTime = (date) => {
    const options = {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }
    
    const formatter = new Intl.DateTimeFormat('en-IN', options)
    const parts = formatter.formatToParts(date)
    
    const dateStr = `${parts.find(p => p.type === 'day').value}/${parts.find(p => p.type === 'month').value}/${parts.find(p => p.type === 'year').value}`
    const timeStr = `${parts.find(p => p.type === 'hour').value}:${parts.find(p => p.type === 'minute').value}:${parts.find(p => p.type === 'second').value} ${parts.find(p => p.type === 'dayPeriod').value}`
    
    return { dateStr, timeStr }
  }

  const formatSimpleIST = (date) => {
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  }

  const { dateStr, timeStr } = formatISTTime(currentTime)

  return (
    <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
      <Clock className="h-4 w-4 text-gray-500 dark:text-gray-400" />
      <div className="text-sm">
        <div className="font-medium text-gray-900 dark:text-gray-100">
          {dateStr}
        </div>
        <div className="text-gray-600 dark:text-gray-300 font-mono">
          {timeStr} IST
        </div>
      </div>
    </div>
  )
}
