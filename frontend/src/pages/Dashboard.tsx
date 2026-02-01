import { useState, useEffect } from 'react'
import { 
  BookOpen, Upload, History, Settings, Send, LogOut, 
  Menu, X, ChevronRight, FileText, Clock, CheckCircle, Trash2, AlertCircle
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'
import UploadZone from '@/components/UploadZone'
import ConversionStatus from '@/components/ConversionStatus'
import { getConversionHistory, deleteConversion, type ConversionHistoryResponse } from '@/services/api'

export interface ConversionJob {
  jobId: string
  fileId: string
  filename: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  epubUrl?: string
  error?: string
}

const sidebarItems = [
  { id: 'convert', label: 'Convert PDF', icon: Upload },
  { id: 'history', label: 'History', icon: History },
  { id: 'kindle', label: 'Send to Kindle', icon: Send, badge: 'Soon' },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('convert')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentJob, setCurrentJob] = useState<ConversionJob | null>(null)
  const [historyData, setHistoryData] = useState<ConversionHistoryResponse | null>(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [deletingJobs, setDeletingJobs] = useState<Set<string>>(new Set())
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // Load history when switching to history tab
  useEffect(() => {
    if (activeTab === 'history' && !historyData) {
      loadHistory()
    }
  }, [activeTab])

  const loadHistory = async () => {
    setLoadingHistory(true)
    try {
      const data = await getConversionHistory()
      setHistoryData(data)
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this conversion?')) {
      return
    }

    setDeletingJobs(prev => new Set(prev).add(jobId))
    try {
      await deleteConversion(jobId)
      // Reload history after deletion
      await loadHistory()
    } catch (error) {
      console.error('Failed to delete conversion:', error)
      alert('Failed to delete conversion')
    } finally {
      setDeletingJobs(prev => {
        const next = new Set(prev)
        next.delete(jobId)
        return next
      })
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside 
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          ${sidebarOpen ? 'w-64' : 'w-0 lg:w-20'}
          bg-white border-r border-gray-200 transition-all duration-300 overflow-hidden
          flex flex-col
        `}
      >
        {/* Logo */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="bg-primary-500 p-2 rounded-lg flex-shrink-0">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            {sidebarOpen && (
              <div className="overflow-hidden">
                <h1 className="text-xl font-bold text-gray-900 whitespace-nowrap">CleanRead</h1>
                <p className="text-xs text-gray-500 whitespace-nowrap">PDF to EPUB</p>
              </div>
            )}
          </div>
        </div>

        {/* User Info */}
        {sidebarOpen && user && (
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-primary-600 font-semibold">
                  {user.full_name?.[0] || user.email[0].toUpperCase()}
                </span>
              </div>
              <div className="overflow-hidden">
                <p className="font-medium text-gray-900 truncate">
                  {user.full_name || 'User'}
                </p>
                <p className="text-sm text-gray-500 truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-colors
                ${activeTab === item.id 
                  ? 'bg-primary-50 text-primary-600' 
                  : 'text-gray-600 hover:bg-gray-100'}
              `}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge && (
                    <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                  {activeTab === item.id && <ChevronRight className="w-4 h-4" />}
                </>
              )}
            </button>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 lg:px-8 py-4 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg lg:hidden"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg hidden lg:block"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold text-gray-900">
              {sidebarItems.find(i => i.id === activeTab)?.label || 'Dashboard'}
            </h1>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 p-4 lg:p-8 overflow-auto">
          {activeTab === 'convert' && (
            <div className="max-w-4xl mx-auto">
              {/* Upload Zone */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6 lg:p-8">
                <div className="mb-8">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                    Convert PDF to EPUB
                  </h2>
                  <p className="text-gray-600 mb-4">
                    Transform your PDFs into beautifully formatted EPUB files optimized for e-readers.
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex gap-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                          💡
                        </div>
                      </div>
                      <div className="text-sm text-gray-700">
                        <p className="font-medium text-gray-900 mb-1">Quick Tips:</p>
                        <ul className="space-y-1">
                          <li>• Works best with text-based PDFs (not scanned images)</li>
                          <li>• Supports files up to 50MB</li>
                          <li>• Processing typically takes 30-60 seconds</li>
                          <li>• You have 50MB storage quota</li>
                          <li>• Files are automatically deleted after 2 weeks</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
                
                {currentJob && currentJob.status !== 'error' ? (
                  <ConversionStatus job={currentJob} />
                ) : (
                  <UploadZone currentJob={currentJob} setCurrentJob={setCurrentJob} />
                )}
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">Conversion History</h2>
                  <p className="text-sm text-gray-500 mt-1">Your recent PDF to EPUB conversions</p>
                  {historyData?.retention_notice && (
                    <div className="mt-3 flex items-start gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      <span>{historyData.retention_notice}</span>
                    </div>
                  )}
                </div>
                
                {loadingHistory ? (
                  <div className="p-8 text-center text-gray-500">
                    <Clock className="w-8 h-8 animate-spin mx-auto mb-2" />
                    <p>Loading history...</p>
                  </div>
                ) : historyData && historyData.jobs.length > 0 ? (
                  <div className="divide-y divide-gray-200">
                    {historyData.jobs.map((job) => {
                      const isDeleting = deletingJobs.has(job.id)
                      const date = new Date(job.created_at).toLocaleDateString()
                      const fileSize = (job.file_size / 1024 / 1024).toFixed(1)
                      
                      return (
                        <div 
                          key={job.id} 
                          className={`p-4 flex items-center justify-between hover:bg-gray-50 ${isDeleting ? 'opacity-50' : ''}`}
                        >
                          <div className="flex items-center gap-4">
                            <div className="bg-gray-100 p-2 rounded-lg">
                              <FileText className="w-5 h-5 text-gray-600" />
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{job.filename}</p>
                              <p className="text-sm text-gray-500">{date} • {fileSize}MB</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {job.status === 'COMPLETED' && (
                              <span className="text-sm text-green-600 flex items-center gap-1">
                                <CheckCircle className="w-4 h-4" />
                                Completed
                              </span>
                            )}
                            {job.status === 'PROCESSING' && (
                              <span className="text-sm text-blue-600 flex items-center gap-1">
                                <Clock className="w-4 h-4 animate-spin" />
                                Processing
                              </span>
                            )}
                            {job.status === 'FAILED' && (
                              <span className="text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                Failed
                              </span>
                            )}
                            {job.epub_url && (
                              <a
                                href={`http://localhost:8000${job.epub_url}`}
                                className="px-3 py-1.5 text-sm bg-primary-50 text-primary-600 rounded-lg hover:bg-primary-100 transition-colors"
                              >
                                Download
                              </a>
                            )}
                            <button
                              onClick={() => handleDeleteJob(job.id)}
                              disabled={isDeleting}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                              title="Delete conversion"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    <History className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="font-medium text-gray-700">No conversions yet</p>
                    <p className="text-sm">Convert your first PDF to get started!</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'kindle' && (
            <div className="max-w-3xl mx-auto py-12">
              <div className="bg-white rounded-2xl border border-gray-200 p-8">
                <div className="text-center mb-8">
                  <Send className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">Send to Kindle</h2>
                  <p className="text-gray-500 mb-6">
                    This feature is coming soon! You'll be able to send converted EPUBs directly to your Kindle.
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-6 mb-6">
                  <p className="font-medium mb-3 text-gray-900">How it will work:</p>
                  <ol className="space-y-2 list-decimal list-inside text-gray-600">
                    <li>Log in to your account</li>
                    <li>Select file from your device</li>
                    <li>Send it to your Kindle</li>
                  </ol>
                </div>

                <div className="border-t border-gray-200 pt-6">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    Setup Your Send to Kindle Email
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Choose your Amazon region to approve your CleanRead email address. The link depends on where your Amazon account is registered.
                  </p>
                  
                  <div className="grid sm:grid-cols-2 gap-3">
                    {[
                      { country: '🇺🇸 United States', domain: 'amazon.com' },
                      { country: '🇬🇧 United Kingdom', domain: 'amazon.co.uk' },
                      { country: '🇩🇪 Germany', domain: 'amazon.de' },
                      { country: '🇫🇷 France', domain: 'amazon.fr' },
                      { country: '🇮🇹 Italy', domain: 'amazon.it' },
                      { country: '🇪🇸 Spain', domain: 'amazon.es' },
                      { country: '🇨🇦 Canada', domain: 'amazon.ca' },
                      { country: '🇦🇺 Australia', domain: 'amazon.com.au' },
                      { country: '🇯🇵 Japan', domain: 'amazon.co.jp' },
                      { country: '🇮🇳 India', domain: 'amazon.in' },
                      { country: '🇧🇷 Brazil', domain: 'amazon.com.br' },
                      { country: '🇲🇽 Mexico', domain: 'amazon.com.mx' },
                    ].map((region) => (
                      <a
                        key={region.domain}
                        href={`https://www.${region.domain}/sendtokindle`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all group"
                      >
                        <span className="text-sm text-gray-700 group-hover:text-primary-700">
                          {region.country}
                        </span>
                        <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-primary-500" />
                      </a>
                    ))}
                  </div>

                  <p className="text-xs text-gray-500 mt-4">
                    💡 Tip: After clicking your region, go to "Preferences" and add our email to your approved sender list.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Account Settings</h2>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      disabled
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      defaultValue={user?.full_name || ''}
                      placeholder="Enter your name"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                    />
                  </div>

                  <button className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium">
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
