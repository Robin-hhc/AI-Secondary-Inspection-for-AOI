import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

// 认证API
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/profile')
}

// 标注API
export const annotationAPI = {
  getPending: (params) => api.get('/annotation/pending', { params }),
  submit: (data) => api.post('/annotation/submit', data),
  getHistory: (params) => api.get('/annotation/history', { params }),
  getDetail: (id) => api.get(`/annotation/${id}`)
}

// 模型API
export const modelAPI = {
  getList: () => api.get('/model/list'),
  switch: (data) => api.post('/model/switch', data),
  add: (data) => api.post('/model/add', data),
  getActive: () => api.get('/model/active')
}

// 统计API
export const statisticsAPI = {
  getOverview: () => api.get('/statistics/overview'),
  getPerformance: (params) => api.get('/statistics/performance', { params }),
  getLabeling: (params) => api.get('/statistics/labeling', { params })
}

export default api
