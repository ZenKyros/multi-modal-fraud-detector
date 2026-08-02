import axios from 'axios'
import { API_URL } from '../utils/constants'

export const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
})

export const uploadAudio = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const analyzeText = (text) => {
  return api.post('/api/analyze_text', { text })
}

export const getHealth = () => {
  return api.get('/api/health')
}