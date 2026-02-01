import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import type { ConversionJob } from '@/components/UploadZone'

interface ConversionStatusProps {
  job: ConversionJob
}

export default function ConversionStatus({ job }: ConversionStatusProps) {
  const getStatusIcon = () => {
    switch (job.status) {
      case 'uploading':
        return <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
      case 'processing':
        return <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-12 h-12 text-green-500" />
      case 'error':
        return <AlertCircle className="w-12 h-12 text-red-500" />
    }
  }

  const getStatusText = () => {
    switch (job.status) {
      case 'uploading':
        return 'Uploading your PDF...'
      case 'processing':
        return 'Converting to EPUB...'
      case 'completed':
        return 'Conversion complete!'
      case 'error':
        return 'Conversion failed'
    }
  }

  const getStatusDescription = () => {
    switch (job.status) {
      case 'uploading':
        return 'Please wait while we upload your file'
      case 'processing':
        return 'This may take a few moments depending on file size'
      case 'completed':
        return 'Your EPUB file is ready to download'
      case 'error':
        return job.error || 'An error occurred during conversion'
    }
  }

  const handleDownload = () => {
    if (job.epubUrl) {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      window.open(`${apiUrl}${job.epubUrl}`, '_blank')
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          {getStatusIcon()}
        </div>

        <h3 className="text-2xl font-bold mb-2 text-gray-900">
          {getStatusText()}
        </h3>
        
        <p className="text-gray-600 mb-2">
          {job.filename}
        </p>

        <p className="text-gray-500 mb-6">
          {getStatusDescription()}
        </p>

        {job.status === 'completed' && job.epubUrl && (
          <button
            onClick={handleDownload}
            className="inline-flex items-center gap-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            <Download className="w-5 h-5" />
            Download EPUB
          </button>
        )}

        {job.status === 'processing' && (
          <div className="mt-6">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-primary-500 h-2 rounded-full animate-pulse-slow" style={{ width: '60%' }}></div>
            </div>
          </div>
        )}

        {(job.status === 'completed' || job.status === 'error') && (
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-primary-600 hover:text-primary-700 underline"
          >
            Convert another file
          </button>
        )}
      </div>
    </div>
  )
}
