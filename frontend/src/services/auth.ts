import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const authApi = axios.create({
  baseURL: `${API_URL}/api/v1/auth`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface User {
  id: string
  email: string
  full_name: string | null
  kindle_email: string | null
  is_active: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export interface LoginData {
  username: string  // email
  password: string
}

const TOKEN_KEY = 'cleanread_token'
const USER_KEY = 'cleanread_user'
const TRIAL_KEY = 'cleanread_trial_used'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser(): User | null {
  const user = localStorage.getItem(USER_KEY)
  return user ? JSON.parse(user) : null
}

export function setAuthData(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuthData(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function hasUsedTrial(): boolean {
  return localStorage.getItem(TRIAL_KEY) === 'true'
}

export function markTrialUsed(): void {
  localStorage.setItem(TRIAL_KEY, 'true')
}

export async function register(data: RegisterData): Promise<AuthResponse> {
  const response = await authApi.post<AuthResponse>('/register', data)
  setAuthData(response.data.access_token, response.data.user)
  return response.data
}

export async function login(data: LoginData): Promise<AuthResponse> {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)

  const response = await authApi.post<AuthResponse>('/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  setAuthData(response.data.access_token, response.data.user)
  return response.data
}

export async function getMe(): Promise<User> {
  const token = getStoredToken()
  if (!token) throw new Error('Not authenticated')

  const response = await authApi.get<User>('/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return response.data
}

export function logout(): void {
  clearAuthData()
}

// Add auth header to API requests
export function getAuthHeader(): Record<string, string> {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}
