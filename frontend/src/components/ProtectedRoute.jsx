import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, verifyToken } = useAuthStore()
  const [isVerifying, setIsVerifying] = useState(true)
  const location = useLocation()

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated) {
        const isValid = await verifyToken()
        if (!isValid) {
          setIsVerifying(false)
          return
        }
      }
      setIsVerifying(false)
    }

    checkAuth()
  }, [isAuthenticated, verifyToken])

  if (isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
