import { useCallback, useState } from 'react'
import { Upload, File, X } from 'lucide-react'
import { uploadFile, convertPDF } from '@/services/api'

export interface ConversionJob {
  jobId: string
  fileId: string
  filename: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  epubUrl?: string
  error?: string
}

interface UploadZoneProps {
  currentJob: ConversionJob | null
  setCurrentJob: (job: ConversionJob | null) => void
}

export default function UploadZone({ currentJob, setCurrentJob }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    const pdfFile = files.find(f => f.type === 'application/pdf')
    
    if (pdfFile) {
      setSelectedFile(pdfFile)
      setError(null)
    } else {
      setError('Please drop a PDF file')
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0]) {
      setSelectedFile(files[0])
      setError(null)
    }
  }, [])

  const handleConvert = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setError(null)

    try {
      // Upload file
      setCurrentJob({
        jobId: '',
        fileId: '',
        filename: selectedFile.name,
        status: 'uploading',
      })

      const uploadResult = await uploadFile(selectedFile)
      
      // Convert to EPUB
      setCurrentJob({
        jobId: '',
        fileId: uploadResult.file_id,
        filename: selectedFile.name,
        status: 'processing',
      })

      const conversionResult = await convertPDF(uploadResult.file_id)
      
      setCurrentJob({
        jobId: conversionResult.job_id,
        fileId: uploadResult.file_id,
        filename: selectedFile.name,
        status: 'completed',
        epubUrl: conversionResult.epub_url,
      })

      setSelectedFile(null)
    } catch (err: any) {
      console.error('Conversion error:', err)
      setError(err.message || 'Conversion failed')
      setCurrentJob({
        jobId: '',
        fileId: '',
        filename: selectedFile.name,
        status: 'error',
        error: err.message || 'Conversion failed',
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setError(null)
  }

  if (currentJob && currentJob.status !== 'error') {
    return null
  }

  return (
    <div className="w-full">
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
          id="file-upload"
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
              htmlFor="file-upload"
              className="inline-block px-6 py-3 bg-primary-500 text-white rounded-lg cursor-pointer hover:bg-primary-600 transition-colors"
            >
              Choose File
            </label>
            <p className="text-sm text-gray-400 mt-4">
              Maximum file size: 50MB
            </p>
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
                disabled={isUploading}
                className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Converting...' : 'Convert to EPUB'}
              </button>
              <button
                onClick={handleClear}
                disabled={isUploading}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}
    </div>
  )
}
