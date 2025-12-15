import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 事件配置相关API
export const eventAPI = {
  // 获取所有事件
  getEvents() {
    return api.get('/events')
  },

  // 获取单个事件
  getEvent(eventId) {
    return api.get(`/events/${eventId}`)
  },

  // 创建事件
  createEvent(data) {
    return api.post('/events', data)
  },

  // 更新事件
  updateEvent(eventId, data) {
    return api.post(`/events/${eventId}`, data)
  },

  // 删除事件
  deleteEvent(eventId) {
    return api.delete(`/events/${eventId}`)
  }
}

// 游戏状态API
export const gameAPI = {
  // 获取当前游戏状态
  getGameState() {
    return api.get('/game-state')
  }
}

// YCY IM 配置API
export const imAPI = {
  // 获取 IM 配置
  getConfig() {
    return api.get('/im-config')
  },

  // 保存 IM 配置
  saveConfig(data) {
    return api.post('/im-config', data)
  },

  // 测试 IM 连接
  testConnection() {
    return api.post('/im-test')
  }
}

export default api
