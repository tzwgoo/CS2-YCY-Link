/**
 * WebSocket URL 生成工具
 * 优先使用环境变量配置，其次使用 window.location
 */

export const getWebSocketUrl = (path) => {
  // 优先使用环境变量配置
  const envUrl = import.meta.env.VITE_WS_BASE_URL
  if (envUrl) {
    // 移除末尾的斜杠，确保路径正确
    const baseUrl = envUrl.endsWith('/') ? envUrl.slice(0, -1) : envUrl
    return `${baseUrl}${path}`
  }

  // 回退到使用 window.location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${path}`
}

export const GAME_STATE_WS_PATH = '/ws/game-state'
export const GAME_EVENTS_WS_PATH = '/ws/game-events'
