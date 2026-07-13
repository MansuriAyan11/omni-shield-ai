import apiClient from './axios'

// Auth APIs
export const authAPI = {
  login: (email: string, password: string) => {
    // OAuth2PasswordRequestForm expects URL-encoded form data with "username" field
    const params = new URLSearchParams()
    params.append('username', email) // OAuth2 uses "username" field
    params.append('password', password)
    
    return apiClient.post('/auth/login', params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  
  register: (email: string, password: string) =>
    apiClient.post('/auth/register', { email, password }, {
      headers: {
        'Content-Type': 'application/json',
      },
    }),
  
  logout: () => apiClient.post('/auth/logout'),
  
  googleAuth: () => apiClient.get('/auth/google'),
}

// Moderation APIs
export const moderationAPI = {
  moderateImage: (formData: FormData) =>
    apiClient.post('/moderate/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  moderateComprehensive: (formData: FormData) =>
    apiClient.post('/moderate/image/comprehensive', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  moderateMultiModel: (formData: FormData) =>
    apiClient.post('/moderate/multi-model', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  moderateURL: (imageUrl: string) =>
    apiClient.post('/moderate/url', { image_url: imageUrl }, {
      headers: {
        'Content-Type': 'application/json',
      },
    }),

  moderateVideo: (formData: FormData) =>
    apiClient.post('/moderate/video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),

  getVideoModerationStatus: (jobId: string) =>
    apiClient.get(`/moderate/video/${jobId}`),
}

// API Key Management
export const keyAPI = {
  createKey: (name: string) =>
    apiClient.post('/keys', { name }, {
      headers: {
        'Content-Type': 'application/json',
      },
    }),
  
  listKeys: () => apiClient.get('/keys'),
  
  revokeKey: (keyId: string) =>
    apiClient.delete(`/keys/${keyId}`),
}

// Analytics APIs
export const analyticsAPI = {
  getStats: () => apiClient.get('/analytics/stats'),
  
  getTimeSeries: (days: number = 7) =>
    apiClient.get(`/analytics/timeseries?days=${days}`),
  
  getLogs: (limit: number = 100, offset: number = 0) =>
    apiClient.get(`/analytics/logs?limit=${limit}&offset=${offset}`),
}

export default {
  auth: authAPI,
  moderation: moderationAPI,
  keys: keyAPI,
  analytics: analyticsAPI,
}
