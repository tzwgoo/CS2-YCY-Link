<template>
  <div class="dashboard">
    <div class="header">
      <h1>CS2-YCY-Link 控制面板</h1>
      <a-space>
        <a-badge :status="imConnected ? 'success' : 'error'" :text="imConnected ? 'IM 已连接' : 'IM 未连接'" />
        <a-badge :status="wsConnected ? 'success' : 'error'" :text="wsConnected ? '后端已连接' : '后端未连接'" />
      </a-space>
    </div>

    <a-row :gutter="[16, 16]">
      <!-- 左侧：IM 连接和游戏状态 -->
      <a-col :xs="24" :lg="8">
        <!-- IM 连接卡片 -->
        <a-card title="IM 连接" size="small" style="margin-bottom: 16px">
          <a-space direction="vertical" style="width: 100%" :size="8">
            <a-statistic
              title="连接状态"
              :value="imConnected ? '已连接' : '未连接'"
              :value-style="{ color: imConnected ? '#3f8600' : '#cf1322', fontSize: '16px' }"
            />

            <a-divider style="margin: 8px 0" />

            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="UID">{{ uid || '未设置' }}</a-descriptions-item>
              <a-descriptions-item label="消息数">{{ messageCount }}</a-descriptions-item>
            </a-descriptions>

            <a-button type="primary" block @click="showConfigModal" size="small">
              配置 UID/Token
            </a-button>
          </a-space>
        </a-card>

        <!-- 游戏状态卡片 -->
        <a-card title="游戏状态" size="small">
          <a-space direction="vertical" style="width: 100%" :size="8">
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="玩家状态">
                <a-tag :color="gameState.is_alive ? 'green' : 'red'" size="small">
                  {{ gameState.is_alive ? '存活' : '死亡' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="当前血量">
                <a-progress
                  :percent="gameState.health"
                  :status="gameState.health > 50 ? 'success' : gameState.health > 20 ? 'normal' : 'exception'"
                  size="small"
                />
              </a-descriptions-item>
              <a-descriptions-item label="回合阶段">
                <a-tag color="blue" size="small">{{ getRoundPhaseText(gameState.round_phase) }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="状态效果">
                <a-space size="small">
                  <a-tag v-if="gameState.flashed > 0" color="orange" size="small">致盲</a-tag>
                  <a-tag v-if="gameState.smoked > 0" color="purple" size="small">烟雾</a-tag>
                  <a-tag v-if="gameState.burning > 0" color="red" size="small">燃烧</a-tag>
                  <a-tag v-if="!gameState.flashed && !gameState.smoked && !gameState.burning" size="small">正常</a-tag>
                </a-space>
              </a-descriptions-item>
            </a-descriptions>
          </a-space>
        </a-card>
      </a-col>

      <!-- 中间：事件配置 -->
      <a-col :xs="24" :lg="10">
        <a-card title="事件配置" size="small">
          <template #extra>
            <a-space size="small">
              <a-button size="small" @click="loadEvents">
                <template #icon><ReloadOutlined /></template>
              </a-button>
            </a-space>
          </template>

          <a-table
            :columns="eventColumns"
            :data-source="eventList"
            :loading="eventsLoading"
            :pagination="{ pageSize: 5, size: 'small' }"
            size="small"
            :scroll="{ y: 400 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'enabled'">
                <a-switch
                  v-model:checked="record.enabled"
                  size="small"
                  @change="toggleEvent(record)"
                />
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space size="small">
                  <a-tag v-for="(action, idx) in record.actions" :key="idx" color="green" size="small">
                    {{ action.command }}
                  </a-tag>
                </a-space>
              </template>
              <template v-else-if="column.key === 'operation'">
                <a-space size="small">
                  <a-tooltip title="测试发送指令">
                    <a-button
                      type="link"
                      size="small"
                      @click="testSendCommand(record)"
                      :disabled="!imConnected"
                    >
                      <template #icon><ThunderboltOutlined /></template>
                    </a-button>
                  </a-tooltip>
                  <a-button type="link" size="small" @click="editEvent(record)">编辑</a-button>
                  <a-popconfirm title="确定删除?" @confirm="deleteEvent(record.id)">
                    <a-button type="link" danger size="small">删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- 右侧：日志 -->
      <a-col :xs="24" :lg="6">
        <a-card title="指令日志" size="small">
          <div style="height: 500px; overflow-y: auto">
            <a-timeline mode="left" style="margin-top: 8px">
              <a-timeline-item
                v-for="(log, index) in commandLogs"
                :key="index"
                :color="log.status === 'success' ? 'green' : 'red'"
              >
                <template #dot>
                  <CheckCircleOutlined v-if="log.status === 'success'" style="font-size: 12px" />
                  <CloseCircleOutlined v-else style="font-size: 12px" />
                </template>
                <div style="font-size: 12px">
                  <div style="color: #999">{{ log.time }}</div>
                  <div>{{ log.command }}</div>
                </div>
              </a-timeline-item>
            </a-timeline>
            <a-empty v-if="commandLogs.length === 0" :image="simpleImage" description="暂无日志" />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- IM 配置模态框 -->
    <a-modal
      v-model:open="configModalVisible"
      title="配置 UID 和 Token"
      @ok="saveConfig"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="UID">
          <a-input
            v-model:value="configForm.uid"
            placeholder="请输入 UID"
          />
        </a-form-item>
        <a-form-item label="Token">
          <a-input-password
            v-model:value="configForm.token"
            placeholder="请输入 Token"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 事件编辑模态框 -->
    <a-modal
      v-model:open="eventModalVisible"
      :title="isEdit ? '编辑事件' : '创建事件'"
      width="700px"
      @ok="handleEventSubmit"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="事件ID" v-if="!isEdit">
          <a-input v-model:value="eventForm.event_id" placeholder="例如: custom_event_1" />
        </a-form-item>
        <a-form-item label="事件名称">
          <a-input v-model:value="eventForm.event_name" placeholder="例如: 玩家受伤" />
        </a-form-item>
        <a-form-item label="启用状态">
          <a-switch v-model:checked="eventForm.enabled" />
        </a-form-item>
        <a-form-item label="触发类型">
          <a-select v-model:value="eventForm.trigger_condition.type">
            <a-select-option value="health_decrease">血量减少</a-select-option>
            <a-select-option value="health_zero">血量归零</a-select-option>
            <a-select-option value="flashed">闪光弹</a-select-option>
            <a-select-option value="smoked">烟雾弹</a-select-option>
            <a-select-option value="burning">燃烧伤害</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="指令内容">
          <a-input
            v-model:value="eventForm.actions[0].command"
            placeholder="例如: player_hurt"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { message, Empty } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons-vue'
import { eventAPI } from '@/api'
import imClient from '@/utils/imClient'
import { getWebSocketUrl, GAME_EVENTS_WS_PATH, GAME_STATE_WS_PATH } from '@/utils/wsUrl'

const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

// IM 连接状态
const imConnected = ref(false)
const uid = ref('')
const messageCount = ref(0)
const configModalVisible = ref(false)
const configForm = reactive({
  uid: '',
  token: ''
})

// 游戏状态
const wsConnected = ref(false)
const gameState = reactive({
  health: 100,
  is_alive: true,
  flashed: 0,
  smoked: 0,
  burning: 0,
  round_phase: 'unknown',
  map_phase: 'unknown'
})

// 事件配置
const eventsLoading = ref(false)
const eventList = ref([])
const eventModalVisible = ref(false)
const isEdit = ref(false)
const eventForm = reactive({
  event_id: '',
  event_name: '',
  enabled: true,
  trigger_condition: {
    type: 'health_decrease'
  },
  actions: [{
    type: 'send_command',
    command: ''
  }]
})

const eventColumns = [
  { title: '事件', dataIndex: 'event_name', key: 'event_name', width: 100 },
  { title: '指令', key: 'actions', width: 100 },
  { title: '启用', key: 'enabled', width: 60 },
  { title: '操作', key: 'operation', width: 140 }
]

// 指令日志
const commandLogs = ref([])

// WebSocket
let ws = null
let gameWs = null

onMounted(() => {
  loadStatus()
  loadEvents()
  connectWebSocket()
  connectGameWebSocket()

  // 监听浏览器窗口关闭事件
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(async () => {
  // 移除事件监听器
  window.removeEventListener('beforeunload', handleBeforeUnload)

  // 关闭 WebSocket 连接
  if (ws) ws.close()
  if (gameWs) gameWs.close()

  // 断开 IM 连接
  await disconnectIM()
})

// 断开 IM 连接的函数
const disconnectIM = async () => {
  try {
    await imClient.disconnect()
    console.log('✓ IM 已断开连接')
  } catch (error) {
    console.error('断开 IM 连接失败:', error)
  }
}

// 处理浏览器窗口关闭
const handleBeforeUnload = (event) => {
  // 同步断开 IM 连接
  if (imClient.chat) {
    try {
      // 使用同步方式尝试断开连接
      imClient.disconnect()
    } catch (error) {
      console.error('窗口关闭时断开 IM 失败:', error)
    }
  }
}

// IM 连接相关
const loadStatus = () => {
  const status = imClient.getStatus()
  imConnected.value = status.isConnected
  uid.value = status.userId || '未设置'
}

const showConfigModal = () => {
  configForm.uid = uid.value === '未设置' ? '' : uid.value
  configForm.token = ''
  configModalVisible.value = true
}

const saveConfig = async () => {
  if (!configForm.uid || !configForm.token) {
    message.error('请填写完整的 UID 和 Token')
    return
  }

  try {
    const hide = message.loading('正在连接 IM...', 0)
    const result = await imClient.connect(configForm.uid, configForm.token)
    hide()

    if (result.success) {
      message.success('IM 连接成功')
      configModalVisible.value = false
      loadStatus()
      addLog('IM 连接成功', 'success')
    } else {
      message.error(result.message || 'IM 连接失败')
    }
  } catch (error) {
    message.error('连接失败')
  }
}

// 事件配置相关
const loadEvents = async () => {
  eventsLoading.value = true
  try {
    const res = await eventAPI.getEvents()
    eventList.value = Object.entries(res.events).map(([id, config]) => ({
      id,
      ...config
    }))
  } catch (error) {
    message.error('加载事件列表失败')
  } finally {
    eventsLoading.value = false
  }
}

const showCreateModal = () => {
  isEdit.value = false
  resetEventForm()
  eventModalVisible.value = true
}

const editEvent = (record) => {
  isEdit.value = true
  Object.assign(eventForm, {
    event_id: record.id,
    event_name: record.event_name,
    enabled: record.enabled,
    trigger_condition: { ...record.trigger_condition },
    actions: JSON.parse(JSON.stringify(record.actions))
  })
  eventModalVisible.value = true
}

const deleteEvent = async (eventId) => {
  try {
    await eventAPI.deleteEvent(eventId)
    message.success('删除成功')
    loadEvents()
  } catch (error) {
    message.error('删除失败')
  }
}

const toggleEvent = async (record) => {
  try {
    await eventAPI.updateEvent(record.id, record)
    message.success('更新成功')
  } catch (error) {
    message.error('更新失败')
    record.enabled = !record.enabled
  }
}

const testSendCommand = async (record) => {
  if (!imConnected.value) {
    message.warning('IM 未连接，无法发送测试指令')
    return
  }

  const actions = record.actions || []
  if (actions.length === 0) {
    message.warning('该事件没有配置指令')
    return
  }

  const hide = message.loading('正在发送测试指令...', 0)

  try {
    for (const action of actions) {
      if (action.type === 'send_command') {
        const commandId = action.command

        const result = await imClient.sendCommand(commandId)
        if (result.success) {
          addLog(`[测试] ${commandId}`, 'success')
          messageCount.value++
        } else {
          addLog(`[测试失败] ${commandId}`, 'error')
        }
      }
    }
    hide()
    message.success('测试指令发送成功')
  } catch (error) {
    hide()
    message.error('测试指令发送失败')
    addLog(`[测试异常] ${record.event_name}`, 'error')
  }
}

const handleEventSubmit = async () => {
  try {
    if (isEdit.value) {
      await eventAPI.updateEvent(eventForm.event_id, eventForm)
      message.success('更新成功')
    } else {
      await eventAPI.createEvent(eventForm)
      message.success('创建成功')
    }
    eventModalVisible.value = false
    loadEvents()
  } catch (error) {
    message.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

const resetEventForm = () => {
  Object.assign(eventForm, {
    event_id: '',
    event_name: '',
    enabled: true,
    trigger_condition: {
      type: 'health_decrease'
    },
    actions: [{
      type: 'send_command',
      command: ''
    }]
  })
}

// WebSocket 连接
const connectWebSocket = () => {
  const wsUrl = getWebSocketUrl(GAME_EVENTS_WS_PATH)
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('✓ WebSocket 已连接')
  }

  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'game_event') {
        await handleGameEvent(data)
      }
    } catch (error) {
      console.error('处理 WebSocket 消息失败:', error)
    }
  }

  ws.onerror = () => {
    console.error('WebSocket 错误')
  }

  ws.onclose = () => {
    console.log('WebSocket 已断开，5秒后重连...')
    setTimeout(connectWebSocket, 5000)
  }
}

const connectGameWebSocket = () => {
  const wsUrl = getWebSocketUrl(GAME_STATE_WS_PATH)
  gameWs = new WebSocket(wsUrl)

  gameWs.onopen = () => {
    wsConnected.value = true
  }

  gameWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'game_state') {
        Object.assign(gameState, data.data)
      }
    } catch (error) {
      console.error('解析游戏状态失败:', error)
    }
  }

  gameWs.onerror = () => {
    wsConnected.value = false
  }

  gameWs.onclose = () => {
    wsConnected.value = false
    setTimeout(connectGameWebSocket, 5000)
  }
}

const handleGameEvent = async (data) => {
  const eventId = data.event_id
  const config = eventList.value.find(e => e.id === eventId)

  if (!config || !config.enabled) {
    return
  }

  const actions = config.actions || []
  for (const action of actions) {
    if (action.type === 'send_command') {
      const commandId = action.command

      if (!imConnected.value) {
        addLog(`发送失败: ${commandId} (IM 未连接)`, 'error')
        return
      }

      try {
        const result = await imClient.sendCommand(commandId)
        if (result.success) {
          addLog(`发送指令: ${commandId}`, 'success')
          messageCount.value++
        } else {
          addLog(`发送失败: ${commandId}`, 'error')
        }
      } catch (error) {
        addLog(`发送异常: ${commandId}`, 'error')
      }
    }
  }
}

const addLog = (command, status) => {
  commandLogs.value.unshift({
    time: new Date().toLocaleTimeString(),
    command,
    status
  })

  if (commandLogs.value.length > 50) {
    commandLogs.value = commandLogs.value.slice(0, 50)
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
</script>

<style scoped>
.dashboard {
  padding: 16px;
  background: #f0f2f5;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px 24px;
  background: #fff;
  border-radius: 4px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
}
</style>
