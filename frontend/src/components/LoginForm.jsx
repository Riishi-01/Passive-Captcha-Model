import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'
import { Eye, EyeOff, Lock } from 'lucide-react'

export default function LoginForm() {
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const { login, loading, error, clearError } = useAuthStore()
  const { addNotification } = useAppStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()

    if (!password.trim()) {
      addNotification({
        type: 'error',
        message: 'Password is required'
      })
      return
    }

    const result = await login(password)
    
    if (result.success) {
      addNotification({
        type: 'success',
        message: 'Login successful'
      })
      navigate('/dashboard')
    } else {
      addNotification({
        type: 'error',
        message: result.error || 'Login failed'
      })
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Admin Password
        </label>
        <div className="mt-1 relative">
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input pr-10"
            placeholder="Enter admin password"
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-gray-400 hover:text-gray-500"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
      </div>

      <div>
        <button
          type="submit"
          disabled={loading}
          className="w-full btn btn-primary h-10 flex items-center justify-center"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <>
              <Lock className="h-4 w-4 mr-2" />
              Sign In
            </>
          )}
        </button>
      </div>
    </form>
  )
}
