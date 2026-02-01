import { useState } from 'react'
import { BookOpen, Smartphone, Zap, Shield, ArrowRight, CheckCircle, Sparkles } from 'lucide-react'
import TrialUpload from '@/components/TrialUpload'
import AuthModal from '@/components/AuthModal'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'

const features = [
  {
    icon: BookOpen,
    title: 'Smart Layout Detection',
    description: 'AI-powered detection handles multi-column layouts, headers, and footers intelligently',
  },
  {
    icon: Smartphone,
    title: 'E-Reader Optimized',
    description: 'Perfect formatting for Kindle and e-ink devices with reflowable text',
  },
  {
    icon: Zap,
    title: 'Fast Processing',
    description: 'GPU-accelerated conversion delivers results in seconds',
  },
  {
    icon: Shield,
    title: 'Privacy First',
    description: 'Your documents are processed securely and deleted after conversion',
  },
]

const benefits = [
  'Unlimited PDF conversions',
  'Conversion history & re-downloads',
  'Send directly to Kindle',
  'Priority processing queue',
  'Batch file conversion',
  'URL article scraping',
]

export default function HomePage() {
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register')
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard')
    } else {
      setAuthMode('register')
      setShowAuthModal(true)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-blue-50" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary-100 rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-100 rounded-full blur-3xl opacity-50 translate-y-1/2 -translate-x-1/2" />
        
        <div className="relative container mx-auto px-4 py-20 lg:py-32">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 rounded-full text-primary-700 text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              AI-Powered PDF to EPUB Conversion
            </div>
            
            <h1 className="text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-gray-900 via-primary-800 to-primary-600 bg-clip-text text-transparent leading-tight">
              Read PDFs Comfortably on Your Kindle
            </h1>
            
            <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
              Transform academic papers, books, and documents into beautifully formatted EPUB files optimized for e-ink readers
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleGetStarted}
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-primary-500 text-white rounded-xl font-semibold hover:bg-primary-600 transition-all shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 hover:-translate-y-0.5"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </button>
              <a
                href="#try-it"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-all border border-gray-200 shadow-sm"
              >
                Try Without Account
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Trial Upload Section */}
      <section id="try-it" className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Try It Now — No Sign Up Required
            </h2>
            <p className="text-lg text-gray-600">
              Convert one PDF for free (up to 5MB). Create an account for unlimited conversions.
            </p>
          </div>
          
          <TrialUpload onSignUpClick={() => {
            setAuthMode('register')
            setShowAuthModal(true)
          }} />
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose CleanRead?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our intelligent conversion engine ensures your documents look great on any e-reader
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100"
              >
                <div className="bg-primary-100 w-12 h-12 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-sm">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-600">
              Three simple steps to better reading
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              { step: 1, title: 'Upload PDF', desc: 'Drag and drop or select your PDF file' },
              { step: 2, title: 'AI Processing', desc: 'Our AI extracts and optimizes content' },
              { step: 3, title: 'Download EPUB', desc: 'Get your e-reader optimized file' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="bg-gradient-to-br from-primary-500 to-primary-600 text-white w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl font-bold shadow-lg shadow-primary-500/25">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold mb-2 text-gray-900">{item.title}</h3>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-primary-500 to-primary-700">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center text-white">
            <h2 className="text-3xl lg:text-4xl font-bold mb-6">
              Ready for Unlimited Conversions?
            </h2>
            <p className="text-xl text-primary-100 mb-8">
              Create a free account and unlock all features
            </p>
            
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10 max-w-2xl mx-auto text-left">
              {benefits.map((benefit) => (
                <div key={benefit} className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-primary-200 flex-shrink-0" />
                  <span className="text-sm">{benefit}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleGetStarted}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-primary-600 rounded-xl font-semibold hover:bg-gray-50 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              Create Free Account
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-primary-500 p-2 rounded-lg">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <span className="text-white font-semibold">CleanRead</span>
            </div>
            <p className="text-sm">
              © 2026 CleanRead. Built with ❤️ for better reading experiences.
            </p>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)}
        initialMode={authMode}
      />
    </div>
  )
}
