import { useState } from 'react'
import { BookOpen, Menu, X } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'
import AuthModal from './AuthModal'

export default function Header() {
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleSignIn = () => {
    setAuthMode('login')
    setShowAuthModal(true)
  }

  const handleSignUp = () => {
    setAuthMode('register')
    setShowAuthModal(true)
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const handleDashboard = () => {
    navigate('/dashboard')
  }

  return (
    <>
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center gap-3">
              <div className="bg-primary-500 p-2 rounded-lg">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">CleanRead</h1>
                <p className="text-sm text-gray-500 hidden sm:block">PDF to EPUB Converter</p>
              </div>
            </a>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-gray-600 hover:text-primary-600 transition-colors">
                Features
              </a>
              <a href="#try-it" className="text-gray-600 hover:text-primary-600 transition-colors">
                Try It
              </a>
              
              {isAuthenticated ? (
                <div className="flex items-center gap-4">
                  <button
                    onClick={handleDashboard}
                    className="px-4 py-2 text-primary-600 font-medium hover:text-primary-700 transition-colors"
                  >
                    Dashboard
                  </button>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <span className="text-primary-600 font-semibold text-sm">
                        {user?.full_name?.[0] || user?.email[0].toUpperCase()}
                      </span>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="text-gray-600 hover:text-gray-900 transition-colors text-sm"
                    >
                      Sign Out
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleSignIn}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={handleSignUp}
                    className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                  >
                    Get Started
                  </button>
                </div>
              )}
            </nav>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 hover:bg-gray-100 rounded-lg"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden mt-4 pb-4 border-t border-gray-200 pt-4">
              <nav className="flex flex-col gap-4">
                <a href="#features" className="text-gray-600 hover:text-primary-600 transition-colors">
                  Features
                </a>
                <a href="#try-it" className="text-gray-600 hover:text-primary-600 transition-colors">
                  Try It
                </a>
                
                {isAuthenticated ? (
                  <>
                    <button
                      onClick={handleDashboard}
                      className="text-left text-primary-600 font-medium"
                    >
                      Dashboard
                    </button>
                    <button
                      onClick={handleLogout}
                      className="text-left text-gray-600"
                    >
                      Sign Out
                    </button>
                  </>
                ) : (
                  <div className="flex flex-col gap-2 pt-2">
                    <button
                      onClick={handleSignIn}
                      className="w-full py-2 text-gray-600 border border-gray-300 rounded-lg"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={handleSignUp}
                      className="w-full py-2 bg-primary-500 text-white rounded-lg"
                    >
                      Get Started
                    </button>
                  </div>
                )}
              </nav>
            </div>
          )}
        </div>
      </header>

      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)}
        initialMode={authMode}
      />
    </>
  )
}
