import { useCallback, useState } from 'react'
import { Upload, File, X, AlertTriangle, CheckCircle, Loader2, Download, Lock } from 'lucide-react'
import { uploadFile, convertPDF } from '@/services/api'
import { hasUsedTrial, markTrialUsed } from '@/services/auth'

interface TrialUploadProps {
  onSignUpClick: () => void
}

const MAX_TRIAL_SIZE = 5 * 1024 * 1024 // 5MB

export default function TrialUpload({ onSignUpClick }: TrialUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const [epubUrl, setEpubUrl] = useState<string | null>(null)
  const trialUsed = hasUsedTrial()

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!trialUsed) setIsDragging(true)
  }, [trialUsed])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (trialUsed) return

    const files = Array.from(e.dataTransfer.files)
    const pdfFile = files.find(f => f.type === 'application/pdf')
    
    if (pdfFile) {
      if (pdfFile.size > MAX_TRIAL_SIZE) {
        setError('Trial is limited to 5MB files. Sign up for larger files!')
        return
      }
      setSelectedFile(pdfFile)
      setError(null)
    } else {
      setError('Please drop a PDF file')
    }
  }, [trialUsed])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (trialUsed) return
    
    const files = e.target.files
    if (files && files[0]) {
      if (files[0].size > MAX_TRIAL_SIZE) {
        setError('Trial is limited to 5MB files. Sign up for larger files!')
        return
      }
      setSelectedFile(files[0])
      setError(null)
    }
  }, [trialUsed])

  const handleConvert = async () => {
    if (!selectedFile || trialUsed) return

    setStatus('uploading')
    setError(null)

    try {
      const uploadResult = await uploadFile(selectedFile)
      
      setStatus('processing')
      const conversionResult = await convertPDF(uploadResult.file_id)
      
      setEpubUrl(conversionResult.epub_url || null)
      setStatus('completed')
      markTrialUsed() // Mark trial as used
      setSelectedFile(null)
    } catch (err: any) {
      console.error('Conversion error:', err)
      setError(err.response?.data?.detail || err.message || 'Conversion failed')
      setStatus('error')
    }
  }

  const handleDownload = () => {
    if (epubUrl) {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      window.open(`${apiUrl}${epubUrl}`, '_blank')
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setError(null)
    setStatus('idle')
  }

  // Trial already used - show sign up prompt
  if (trialUsed && status !== 'completed') {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center">
          <Lock className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-xl font-semibold mb-2 text-gray-700">
            Trial Conversion Used
          </h3>
          <p className="text-gray-500 mb-6">
            You've used your free trial conversion. Create an account for unlimited conversions!
          </p>
          <button
            onClick={onSignUpClick}
            className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium"
          >
            Sign Up for Free
          </button>
        </div>
      </div>
    )
  }

  // Conversion completed
  if (status === 'completed' && epubUrl) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-green-50 border-2 border-green-200 rounded-2xl p-12 text-center">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
          <h3 className="text-xl font-semibold mb-2 text-gray-900">
            Conversion Complete!
          </h3>
          <p className="text-gray-600 mb-6">
            Your EPUB is ready to download
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleDownload}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
            >
              <Download className="w-5 h-5" />
              Download EPUB
            </button>
            <button
              onClick={onSignUpClick}
              className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium"
            >
              Sign Up for More
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Processing/Uploading state
  if (status === 'uploading' || status === 'processing') {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-primary-50 border-2 border-primary-200 rounded-2xl p-12 text-center">
          <Loader2 className="w-16 h-16 mx-auto mb-4 text-primary-500 animate-spin" />
          <h3 className="text-xl font-semibold mb-2 text-gray-900">
            {status === 'uploading' ? 'Uploading...' : 'Converting to EPUB...'}
          </h3>
          <p className="text-gray-600">
            {status === 'uploading' 
              ? 'Please wait while we upload your file' 
              : 'This may take a few moments'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-12 text-center transition-all
          ${isDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 bg-white'}
          ${selectedFile ? 'border-green-500 bg-green-50' : ''}
        `}
      >
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileSelect}
          className="hidden"
          id="trial-file-upload"
        />

        {!selectedFile ? (
          <>
            <Upload className={`w-16 h-16 mx-auto mb-4 ${isDragging ? 'text-primary-500' : 'text-gray-400'}`} />
            <h3 className="text-xl font-semibold mb-2 text-gray-700">
              Drop your PDF here
            </h3>
            <p className="text-gray-500 mb-6">
              or click to browse your files
            </p>
            <label
              htmlFor="trial-file-upload"
              className="inline-block px-6 py-3 bg-primary-500 text-white rounded-lg cursor-pointer hover:bg-primary-600 transition-colors font-medium"
            >
              Choose File
            </label>
            <div className="flex items-center justify-center gap-2 mt-4 text-sm text-gray-400">
              <AlertTriangle className="w-4 h-4" />
              Trial limited to 5MB • One conversion only
            </div>
          </>
        ) : (
          <>
            <File className="w-16 h-16 mx-auto mb-4 text-green-500" />
            <h3 className="text-xl font-semibold mb-2 text-gray-700">
              {selectedFile.name}
            </h3>
            <p className="text-gray-500 mb-6">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleConvert}
                className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium"
              >
                Convert to EPUB
              </button>
              <button
                onClick={handleClear}
                className="p-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  )
}
