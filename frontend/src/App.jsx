import { useState, useEffect } from 'react'
import EligibilityCheck from './components/EligibilityCheck'
import ResultScreen from './components/ResultScreen'
import RecentChecks from './components/RecentChecks'
import EnrollmentFlow from './components/EnrollmentFlow'
import CPSSDashboard from './components/CPSSDashboard'
import VideoSession from './components/VideoSession'
import Login from './components/Login'
import Register from './components/Register'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function AppContent() {
  const [currentScreen, setCurrentScreen] = useState('check') // 'check', 'result', 'enrollment', 'dashboard', 'video', 'login', 'register'
  const [result, setResult] = useState(null)
  const [videoSessionData, setVideoSessionData] = useState(null)
  const { user, isAuthenticated, logout, loading } = useAuth()

  useEffect(() => {
    // If not authenticated, show login screen
    if (!loading && !isAuthenticated) {
      setCurrentScreen('login')
    }
  }, [isAuthenticated, loading])

  const handleLogin = (userData, token) => {
    setCurrentScreen('dashboard')
  }

  const handleRegister = (userData, token) => {
    setCurrentScreen('dashboard')
  }

  const handleLogout = () => {
    logout()
    setCurrentScreen('login')
  }

  const handleResult = (resultData) => {
    setResult(resultData)
    setCurrentScreen('result')
  }

  const handleCheckAnother = () => {
    setResult(null)
    setCurrentScreen('check')
  }

  const handleContinueEnrollment = () => {
    setCurrentScreen('enrollment')
  }

  const handleEnrollmentComplete = (enrollmentData) => {
    // Show success message or confirmation
    alert(`Enrollment complete for ${enrollmentData.patient?.firstName} ${enrollmentData.patient?.lastName}`)
    // Reset to check screen
    setResult(null)
    setCurrentScreen('check')
  }

  const handleEnrollmentCancel = () => {
    // Go back to result screen
    setCurrentScreen('result')
  }

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  // Show login/register screens if not authenticated
  if (!isAuthenticated) {
    if (currentScreen === 'register') {
      return (
        <Register
          onRegister={handleRegister}
          onSwitchToLogin={() => setCurrentScreen('login')}
        />
      )
    }
    return (
      <Login
        onLogin={handleLogin}
        onSwitchToRegister={() => setCurrentScreen('register')}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-gray-800">CM Program</h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => setCurrentScreen('check')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    currentScreen === 'check' || currentScreen === 'result'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Eligibility Check
                </button>
                <button
                  onClick={() => setCurrentScreen('dashboard')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    currentScreen === 'dashboard'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  CPSS Dashboard
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.full_name || user?.username}
              </span>
              <button
                onClick={handleLogout}
                className="px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {currentScreen === 'dashboard' ? (
        <CPSSDashboard />
      ) : currentScreen === 'video' ? (
        <VideoSession
          sessionId={videoSessionData?.sessionId}
          participantId={videoSessionData?.participantId}
          mode={videoSessionData?.mode || 'group'}
        />
      ) : currentScreen === 'enrollment' ? (
        <EnrollmentFlow
          patientData={result}
          onComplete={handleEnrollmentComplete}
          onCancel={handleEnrollmentCancel}
        />
      ) : (
        <div className="py-8">
          <div className="container mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-800">Utah Medicaid Eligibility</h1>
              <p className="text-gray-600 mt-2">Contingency Management Program</p>
            </div>

            {currentScreen === 'check' ? (
              <>
                <EligibilityCheck onResult={handleResult} />
                <RecentChecks />
              </>
            ) : (
              <ResultScreen
                result={result}
                onCheckAnother={handleCheckAnother}
                onContinueEnrollment={handleContinueEnrollment}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
