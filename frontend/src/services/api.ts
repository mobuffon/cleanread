import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
})

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cleanread_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Ensure JSON content-type only when not already set (e.g., for multipart)
  if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json'
  }
  return config
})

export interface UploadResponse {
  file_id: string
  filename: string
  size: number
  message: string
}

export interface ConversionResponse {
  job_id: string
  file_id: string
  status: string
  message: string
  epub_url?: string
}

export interface ConversionRequest {
  file_id: string
  start_page?: number
  max_pages?: number
  languages?: string
  batch_multiplier?: number
}

export interface ConversionHistoryResponse {
  jobs: Array<{
    id: string
    filename: string
    status: string
    created_at: string
    epub_url: string | null
    file_size: number
    processing_time: number | null
  }>
  retention_notice: string
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<UploadResponse>('/upload', formData)

  return response.data
}

export async function convertPDF(
  fileId: string,
  options?: Omit<ConversionRequest, 'file_id'>
): Promise<ConversionResponse> {
  const response = await api.post<ConversionResponse>('/convert', {
    file_id: fileId,
    ...options,
  })

  return response.data
}

export async function getConversionStatus(jobId: string): Promise<ConversionResponse> {
  const response = await api.get<ConversionResponse>(`/convert/status/${jobId}`)
  return response.data
}

export async function getConversionHistory(): Promise<ConversionHistoryResponse> {
  const response = await api.get<ConversionHistoryResponse>('/convert/history')
  return response.data
}

export async function deleteConversion(jobId: string): Promise<void> {
  await api.delete(`/convert/job/${jobId}`)
}

export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}

export default api
