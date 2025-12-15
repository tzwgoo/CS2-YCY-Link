<template>
  <div class="game-monitor">
    <a-space direction="vertical" style="width: 100%" :size="16">
      <a-card title="游戏状态" :loading="loading">
        <a-descriptions bordered :column="2">
          <a-descriptions-item label="连接状态">
            <a-badge
              :status="wsConnected ? 'success' : 'error'"
              :text="wsConnected ? '已连接' : '未连接'"
            />
          </a-descriptions-item>
          <a-descriptions-item label="玩家状态">
            <a-tag :color="gameState.is_alive ? 'green' : 'red'">
              {{ gameState.is_alive ? '存活' : '死亡' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="当前血量">
            <a-progress
              :percent="gameState.health"
              :status="gameState.health > 50 ? 'success' : gameState.health > 20 ? 'normal' : 'exception'"
            />
          </a-descriptions-item>
          <a-descriptions-item label="回合阶段">
            <a-tag color="blue">{{ getRoundPhaseText(gameState.round_phase) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="闪光效果">
            <a-tag :color="gameState.flashed > 0 ? 'orange' : 'default'">
              {{ gameState.flashed > 0 ? '致盲中' : '正常' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="烟雾效果">
            <a-tag :color="gameState.smoked > 0 ? 'purple' : 'default'">
              {{ gameState.smoked > 0 ? '烟雾中' : '正常' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="燃烧伤害">
            <a-tag :color="gameState.burning > 0 ? 'red' : 'default'">
              {{ gameState.burning > 0 ? '燃烧中' : '正常' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="地图阶段">
            <a-tag color="cyan">{{ getMapPhaseText(gameState.map_phase) }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card title="事件日志">
        <a-timeline mode="left">
          <a-timeline-item
            v-for="(log, index) in eventLogs"
            :key="index"
            :color="getLogColor(log.type)"
          >
            <template #dot>
              <ClockCircleOutlined v-if="log.type === 'info'" />
              <CheckCircleOutlined v-if="log.type === 'success'" style="color: #52c41a" />
              <ExclamationCircleOutlined v-if="log.type === 'warning'" style="color: #faad14" />
              <CloseCircleOutlined v-if="log.type === 'error'" style="color: #f5222d" />
            </template>
            <p>{{ log.time }}</p>
            <p>{{ log.message }}</p>
          </a-timeline-item>
        </a-timeline>
        <a-empty v-if="eventLogs.length === 0" description="暂无事件日志" />
      </a-card>
    </a-space>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons-vue'
import { gameAPI } from '@/api'
import { getWebSocketUrl, GAME_STATE_WS_PATH } from '@/utils/wsUrl'

const loading = ref(false)
const wsConnected = ref(false)
let ws = null

const gameState = reactive({
  health: 100,
  is_alive: true,
  flashed: 0,
  smoked: 0,
  burning: 0,
  round_phase: 'unknown',
  map_phase: 'unknown'
})

const eventLogs = ref([])

onMounted(() => {
  loadGameState()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

const loadGameState = async () => {
  loading.value = true
  try {
    const state = await gameAPI.getGameState()
    Object.assign(gameState, state)
  } catch (error) {
    message.error('加载游戏状态失败')
  } finally {
    loading.value = false
  }
}

const connectWebSocket = () => {
  const wsUrl = getWebSocketUrl(GAME_STATE_WS_PATH)

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    wsConnected.value = true
    addLog('info', 'WebSocket连接成功')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'game_state') {
        const oldHealth = gameState.health
        Object.assign(gameState, data.data)

        // 记录重要事件
        if (oldHealth > gameState.health) {
          addLog('warning', `玩家受伤: ${oldHealth} → ${gameState.health}`)
        }
        if (gameState.health === 0 && oldHealth > 0) {
          addLog('error', '玩家死亡')
        }
        if (gameState.flashed > 0) {
          addLog('warning', '被闪光弹致盲')
        }
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  ws.onerror = (error) => {
    wsConnected.value = false
    addLog('error', 'WebSocket连接错误')
    console.error('WebSocket error:', error)
  }

  ws.onclose = () => {
    wsConnected.value = false
    addLog('info', 'WebSocket连接关闭')
    // 5秒后尝试重连
    setTimeout(() => {
      if (!wsConnected.value) {
        connectWebSocket()
      }
    }, 5000)
  }
}

const addLog = (type, message) => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now
    .getMinutes()
    .toString()
    .padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

  eventLogs.value.unshift({
    type,
    time,
    message
  })

  // 只保留最近50条日志
  if (eventLogs.value.length > 50) {
    eventLogs.value.pop()
  }
}

const getRoundPhaseText = (phase) => {
  const phaseMap = {
    over: '回合结束',
    freezetime: '冻结时间',
    live: '进行中',
    unknown: '未知'
  }
  return phaseMap[phase] || phase
}

const getMapPhaseText = (phase) => {
  const phaseMap = {
    warmup: '热身',
    live: '进行中',
    intermission: '中场休息',
    gameover: '游戏结束',
    unknown: '未知'
  }
  return phaseMap[phase] || phase
}

const getLogColor = (type) => {
  const colorMap = {
    info: 'blue',
    success: 'green',
    warning: 'orange',
    error: 'red'
  }
  return colorMap[type] || 'blue'
}
</script>

<style scoped>
.game-monitor {
  width: 100%;
}
</style>
