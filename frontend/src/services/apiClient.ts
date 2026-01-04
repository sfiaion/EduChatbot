import axios from 'axios'

const isDevProxy = typeof window !== 'undefined' && /:\/\/(localhost|127\.0\.0\.1):5173$/.test(window.location.origin)
const baseURL = isDevProxy ? '' : (import.meta.env.VITE_API_BASE_URL || '')

export const api = axios.create({
  baseURL,
  timeout: 30000
})

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token')
            // Redirect to login if not already there
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)
