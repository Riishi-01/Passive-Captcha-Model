import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'
import LoginForm from '../components/LoginForm'

export default function LoginView() {
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard')
    }
  }, [isAuthenticated, navigate])

  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Admin Login
        </h2>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Enter your admin password to access the dashboard
        </p>
      </div>
      
      <LoginForm />
    </div>
  )
}
