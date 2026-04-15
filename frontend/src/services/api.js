import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/web'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  // AQI and Area endpoints
  getArea: (areaId) => api.get(`/area/${areaId}`),
  getAreaAnalysis: (areaId) => api.get(`/area/${areaId}/analysis`),
  getAQI: (areaId) => api.get(`/area/${areaId}/aqi`),
  getAQITrend: (areaId) => api.get(`/area/${areaId}/aqi-trend`),
  
  // Tree recommendations
  getTreeRecommendations: (areaId) => api.get(`/area/${areaId}/trees`),
  
  // Forecasting
  getForecast: (areaId) => api.get(`/area/${areaId}/forecast`),
  getAllForecasts: () => api.get('/forecast-all'),
  
  // Scenario and impact
  simulateScenario: (areaId, targetAQI) => 
    api.post(`/area/${areaId}/scenario`, { targetAQI }),
  estimateImpact: (areaId, treeCount, speciesMix) =>
    api.post(`/area/${areaId}/impact-estimate`, { treeCount, speciesMix }),
  
  // Feedback
  storeFeedback: (cityId, shownTreeIds, selectedTreeIds, note) =>
    api.post('/feedback', { cityId, shownTreeIds, selectedTreeIds, note }),
}

export default api
