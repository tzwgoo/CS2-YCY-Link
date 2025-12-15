<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">
        <h2 v-if="!collapsed">CS2 触发系统</h2>
        <h2 v-else>CS2</h2>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="/events">
          <template #icon>
            <SettingOutlined />
          </template>
          <span>事件配置</span>
        </a-menu-item>
        <a-menu-item key="/monitor">
          <template #icon>
            <DashboardOutlined />
          </template>
          <span>游戏监控</span>
        </a-menu-item>
        <a-menu-item key="/device">
          <template #icon>
            <ApiOutlined />
          </template>
          <span>IM 连接</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 24px">
        <h1 style="margin: 0">{{ currentTitle }}</h1>
      </a-layout-header>
      <a-layout-content style="margin: 16px">
        <div style="padding: 24px; background: #fff; min-height: 360px">
          <router-view />
        </div>
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        CS2-YCY-Link 控制面板 ©2024
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  SettingOutlined,
  DashboardOutlined,
  ApiOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const selectedKeys = ref([route.path])

const currentTitle = computed(() => {
  return route.meta.title || 'CS2-YCY-Link 控制面板'
})

watch(
  () => route.path,
  (newPath) => {
    selectedKeys.value = [newPath]
  }
)

const handleMenuClick = ({ key }) => {
  router.push(key)
}
</script>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
}

.logo h2 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}
</style>
