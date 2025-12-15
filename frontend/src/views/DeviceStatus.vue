<template>
  <div class="device-status">
    <a-space direction="vertical" style="width: 100%" :size="16">
      <a-card title="YCY IM 连接状态">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-statistic
              title="连接状态"
              :value="imConnected ? '已连接' : '未连接'"
              :value-style="{ color: imConnected ? '#3f8600' : '#cf1322' }"
            >
              <template #prefix>
                <ApiOutlined />
              </template>
            </a-statistic>
          </a-col>
          <a-col :span="12">
            <a-statistic title="UID" :value="uid || '未设置'">
              <template #prefix>
                <UserOutlined />
              </template>
            </a-statistic>
          </a-col>
        </a-row>

        <a-divider />

        <a-descriptions bordered :column="2">
          <a-descriptions-item label="API 地址">
            https://suo.jiushu1234.com/api.php
          </a-descriptions-item>
          <a-descriptions-item label="Token 状态">
            <a-tag :color="tokenValid ? 'green' : 'red'">
              {{ tokenValid ? '有效' : '未设置' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="最后心跳">
            {{ lastHeartbeat || '暂无' }}
          </a-descriptions-item>
          <a-descriptions-item label="消息发送数">
            {{ messageCount }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider />

        <a-alert
          v-if="!tokenValid"
          message="首次使用提示"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        >
          <template #description>
            <div>
              <p>欢迎使用CS2-YCY-Link</p>
              <p>请点击下方"配置 UID/Token"按钮，填入你的凭证。</p>
            </div>
          </template>
        </a-alert>

        <a-alert
          v-else-if="!imConnected"
          message="IM 未连接"
          description="配置已保存，请重启后端服务以应用更改"
          type="warning"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-space>
          <a-button type="primary" @click="testConnection">
            <template #icon><SyncOutlined /></template>
            测试连接
          </a-button>
          <a-button @click="showConfigModal">
            <template #icon><SettingOutlined /></template>
            配置 UID/Token
          </a-button>
        </a-space>
      </a-card>

      <a-card title="指令配置">
        <a-descriptions bordered :column="2">
          <a-descriptions-item label="指令格式">
            JSON 格式
          </a-descriptions-item>
          <a-descriptions-item label="API 端点">
            /game/send_command
          </a-descriptions-item>
          <a-descriptions-item label="自动心跳">
            <a-tag color="green">已启用</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="心跳间隔">
            30 秒
          </a-descriptions-item>
        </a-descriptions>

        <a-divider />


      </a-card>

      <a-card title="指令日志">
        <a-table
          :columns="logColumns"
          :data-source="commandLogs"
          :pagination="{ pageSize: 10 }"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : 'red'">
                {{ record.status === 'success' ? '成功' : '失败' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'command'">
              <a-typography-text code>{{ record.command }}</a-typography-text>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-space>

    <!-- 配置模态框 -->
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  ApiOutlined,
  UserOutlined,
  SyncOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'
import { eventAPI } from '@/api'
import imClient from '@/utils/imClient'
import { getWebSocketUrl, GAME_EVENTS_WS_PATH } from '@/utils/wsUrl'

const imConnected = ref(false)
const uid = ref('')
const tokenValid = ref(false)
const lastHeartbeat = ref('')
const messageCount = ref(0)
const ws = ref(null)

const configModalVisible = ref(false)
const configForm = reactive({
  uid: '',
  token: ''
})

const logColumns = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
  { title: '指令', dataIndex: 'command', key: 'command' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 }
]

const commandLogs = ref([])

// 事件配置缓存
const eventConfigs = ref({})

onMounted(() => {
  loadStatus()
  loadEventConfigs()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})

const loadStatus = () => {
  const status = imClient.getStatus()
  imConnected.value = status.isConnected
  uid.value = status.userId || '未设置'
  tokenValid.value = !!status.userId

  if (imConnected.value) {
    lastHeartbeat.value = new Date().toLocaleString()
  }
}

const loadEventConfigs = async () => {
  try {
    const res = await eventAPI.getEvents()
    eventConfigs.value = res.events
    console.log('已加载事件配置:', eventConfigs.value)
  } catch (error) {
    console.error('加载事件配置失败:', error)
  }
}

const connectWebSocket = () => {
  const wsUrl = getWebSocketUrl(GAME_EVENTS_WS_PATH)
  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    console.log('✓ WebSocket 已连接')
    addLog('WebSocket 连接成功', 'success')
  }

  ws.value.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('收到游戏事件:', data)

      if (data.type === 'game_event') {
        await handleGameEvent(data)
      }
    } catch (error) {
      console.error('处理 WebSocket 消息失败:', error)
    }
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket 错误:', error)
    addLog('WebSocket 连接错误', 'error')
  }

  ws.value.onclose = () => {
    console.log('WebSocket 已断开，5秒后重连...')
    addLog('WebSocket 已断开', 'error')
    setTimeout(connectWebSocket, 5000)
  }
}

const handleGameEvent = async (data) => {
  const eventId = data.event_id
  const config = eventConfigs.value[eventId]

  if (!config || !config.enabled) {
    console.log(`事件 ${eventId} 未启用或不存在`)
    return
  }

  // 获取事件配置的指令
  const actions = config.actions || []
  for (const action of actions) {
    if (action.type === 'send_command') {
      const commandId = action.command

      if (!imConnected.value) {
        addLog(`发送指令失败: ${commandId} (IM 未连接)`, 'error')
        message.warning('IM 未连接，无法发送指令')
        return
      }

      try {
        const result = await imClient.sendCommand(commandId)
        if (result.success) {
          addLog(`发送指令: ${commandId}`, 'success')
          messageCount.value++
        } else {
          addLog(`发送指令失败: ${commandId}`, 'error')
        }
      } catch (error) {
        console.error('发送指令失败:', error)
        addLog(`发送指令异常: ${commandId}`, 'error')
      }
    }
  }
}

const addLog = (command, status) => {
  commandLogs.value.unshift({
    time: new Date().toLocaleString(),
    command,
    status
  })

  // 只保留最近 100 条日志
  if (commandLogs.value.length > 100) {
    commandLogs.value = commandLogs.value.slice(0, 100)
  }
}

const testConnection = async () => {
  if (!configForm.uid || !configForm.token) {
    message.error('请先配置 UID 和 Token')
    showConfigModal()
    return
  }

  try {
    const hide = message.loading('正在连接 IM...', 0)
    const result = await imClient.connect(configForm.uid, configForm.token)
    hide()

    if (result.success) {
      message.success('IM 连接成功')
      loadStatus()
      addLog('IM 连接成功', 'success')
    } else {
      message.error(result.message || 'IM 连接失败')
      addLog('IM 连接失败', 'error')
    }
  } catch (error) {
    message.error('连接测试失败')
    addLog('IM 连接异常', 'error')
  }
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
    // 直接连接 IM
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
    console.error('连接失败:', error)
    message.error('连接失败')
  }
}
</script>

<style scoped>
.device-status {
  width: 100%;
}
</style>
