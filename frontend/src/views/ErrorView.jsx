import { useNavigate, useLocation } from 'react-router-dom'
import { AlertTriangle, Home, ArrowLeft } from 'lucide-react'

export default function ErrorView() {
  const navigate = useNavigate()
  const location = useLocation()
  const is404 = location.pathname !== '/error'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 dark:bg-red-900 mb-6">
            <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            {is404 ? '404' : 'Error'}
          </h1>
          
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
            {is404 ? 'Page Not Found' : 'Something went wrong'}
          </h2>
          
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            {is404 
              ? "The page you're looking for doesn't exist or has been moved."
              : "We're sorry, but something unexpected happened. Please try again."
            }
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate(-1)}
              className="btn btn-secondary flex items-center justify-center"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </button>
            
            <button
              onClick={() => navigate('/dashboard')}
              className="btn btn-primary flex items-center justify-center"
            >
              <Home className="h-4 w-4 mr-2" />
              Dashboard
            </button>
          </div>

          {!is404 && (
            <div className="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                Need Help?
              </h3>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                If this error persists, please check the system logs or contact support.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
