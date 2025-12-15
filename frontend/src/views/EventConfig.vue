<template>
  <div class="event-config">
    <a-space direction="vertical" style="width: 100%" :size="16">
      <a-row :gutter="16" justify="space-between" align="middle">
        <a-col>
          <a-space>
            <a-button type="primary" @click="showCreateModal">
              <template #icon><PlusOutlined /></template>
              新建事件
            </a-button>
            <a-button @click="loadEvents">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </a-col>
      </a-row>

      <a-table
        :columns="columns"
        :data-source="eventList"
        :loading="loading"
        row-key="id"
        :pagination="{ pageSize: 10 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'enabled'">
            <a-switch
              v-model:checked="record.enabled"
              @change="toggleEvent(record)"
            />
          </template>
          <template v-else-if="column.key === 'trigger'">
            <a-tag color="blue">{{ getTriggerText(record.trigger_condition) }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-tag v-for="(action, idx) in record.actions" :key="idx" color="green">
                {{ getActionText(action) }}
              </a-tag>
            </a-space>
          </template>
          <template v-else-if="column.key === 'operation'">
            <a-space>
              <a-button type="link" size="small" @click="editEvent(record)">
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个事件吗？"
                @confirm="deleteEvent(record.id)"
              >
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-space>

    <!-- 创建/编辑事件模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑事件' : '创建事件'"
      width="800px"
      @ok="handleSubmit"
      @cancel="handleCancel"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="事件ID" name="event_id" v-if="!isEdit">
          <a-input v-model:value="formData.event_id" placeholder="例如: custom_event_1" />
        </a-form-item>

        <a-form-item label="事件名称" name="event_name">
          <a-input v-model:value="formData.event_name" placeholder="例如: 玩家受伤" />
        </a-form-item>

        <a-form-item label="事件描述" name="description">
          <a-textarea
            v-model:value="formData.description"
            placeholder="描述这个事件的作用"
            :rows="2"
          />
        </a-form-item>

        <a-form-item label="启用状态" name="enabled">
          <a-switch v-model:checked="formData.enabled" />
        </a-form-item>

        <a-divider>触发条件</a-divider>

        <a-form-item label="触发类型" name="trigger_type">
          <a-select v-model:value="formData.trigger_condition.type">
            <a-select-option value="health_decrease">血量减少</a-select-option>
            <a-select-option value="health_zero">血量归零</a-select-option>
            <a-select-option value="flashed">闪光弹</a-select-option>
            <a-select-option value="smoked">烟雾弹</a-select-option>
            <a-select-option value="burning">燃烧伤害</a-select-option>
            <a-select-option value="round_phase">回合阶段</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item
          label="最小伤害"
          v-if="formData.trigger_condition.type === 'health_decrease'"
        >
          <a-input-number
            v-model:value="formData.trigger_condition.min_damage"
            :min="1"
            :max="100"
          />
        </a-form-item>

        <a-form-item
          label="回合阶段"
          v-if="formData.trigger_condition.type === 'round_phase'"
        >
          <a-select v-model:value="formData.trigger_condition.value">
            <a-select-option value="over">结束</a-select-option>
            <a-select-option value="freezetime">冻结时间</a-select-option>
            <a-select-option value="live">进行中</a-select-option>
          </a-select>
        </a-form-item>

        <a-divider>动作配置</a-divider>

        <a-form-item label="动作列表">
          <a-space direction="vertical" style="width: 100%">
            <div
              v-for="(action, index) in formData.actions"
              :key="index"
              style="border: 1px solid #d9d9d9; padding: 12px; border-radius: 4px"
            >
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-select v-model:value="action.type" placeholder="动作类型">
                    <a-select-option value="send_command">发送指令</a-select-option>
                  </a-select>
                </a-col>
                <a-col :span="8">
                  <a-input
                    v-model:value="action.command"
                    placeholder="指令内容（如: player_hurt）"
                  />
                </a-col>
                <a-col :span="6">
                  <a-checkbox v-model:checked="action.include_data">
                    包含游戏数据
                  </a-checkbox>
                </a-col>
                <a-col :span="2">
                  <a-button
                    type="text"
                    danger
                    @click="removeAction(index)"
                  >
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-col>
              </a-row>
            </div>
            <a-button type="dashed" block @click="addAction">
              <template #icon><PlusOutlined /></template>
              添加动作
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { eventAPI } from '@/api'

const loading = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const eventList = ref([])
const formRef = ref()

const columns = [
  { title: '事件名称', dataIndex: 'event_name', key: 'event_name' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '触发条件', key: 'trigger' },
  { title: '动作', key: 'actions' },
  { title: '启用', key: 'enabled', width: 80 },
  { title: '操作', key: 'operation', width: 150 }
]

const formData = reactive({
  event_id: '',
  event_name: '',
  description: '',
  enabled: true,
  trigger_condition: {
    type: 'health_decrease',
    min_damage: 1
  },
  actions: []
})

onMounted(() => {
  loadEvents()
})

const loadEvents = async () => {
  loading.value = true
  try {
    const res = await eventAPI.getEvents()
    eventList.value = Object.entries(res.events).map(([id, config]) => ({
      id,
      ...config
    }))
  } catch (error) {
    message.error('加载事件列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  isEdit.value = false
  resetForm()
  modalVisible.value = true
}

const editEvent = (record) => {
  isEdit.value = true
  Object.assign(formData, {
    event_id: record.id,
    event_name: record.event_name,
    description: record.description,
    enabled: record.enabled,
    trigger_condition: { ...record.trigger_condition },
    actions: JSON.parse(JSON.stringify(record.actions))
  })
  modalVisible.value = true
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
    await eventAPI.updateEvent(record.id, {
      ...record,
      enabled: record.enabled
    })
    message.success('更新成功')
  } catch (error) {
    message.error('更新失败')
    record.enabled = !record.enabled
  }
}

const addAction = () => {
  formData.actions.push({
    type: 'send_command',
    command: '',
    include_data: false
  })
}

const removeAction = (index) => {
  formData.actions.splice(index, 1)
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await eventAPI.updateEvent(formData.event_id, formData)
      message.success('更新成功')
    } else {
      await eventAPI.createEvent(formData)
      message.success('创建成功')
    }
    modalVisible.value = false
    loadEvents()
  } catch (error) {
    message.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

const handleCancel = () => {
  modalVisible.value = false
  resetForm()
}

const resetForm = () => {
  Object.assign(formData, {
    event_id: '',
    event_name: '',
    description: '',
    enabled: true,
    trigger_condition: {
      type: 'health_decrease',
      min_damage: 1
    },
    actions: []
  })
}

const getTriggerText = (trigger) => {
  const typeMap = {
    health_decrease: '血量减少',
    health_zero: '血量归零',
    flashed: '闪光弹',
    smoked: '烟雾弹',
    burning: '燃烧伤害',
    round_phase: '回合阶段'
  }
  return typeMap[trigger.type] || trigger.type
}

const getActionText = (action) => {
  const typeMap = {
    send_command: '发送指令'
  }
  const typeName = typeMap[action.type] || action.type
  const command = action.command || '未设置'
  return `${typeName}: ${command}`
}
</script>

<style scoped>
.event-config {
  width: 100%;
}
</style>
