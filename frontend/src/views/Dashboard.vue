<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElCard, ElButton, ElAvatar, ElTag } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/format'

const authStore = useAuthStore()
const loading = ref(false)

onMounted(async () => {
  if (!authStore.user) {
    loading.value = true
    await authStore.fetchCurrentUser()
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-3xl font-bold text-black mb-6">仪表盘</h1>

    <el-card v-if="authStore.user">
      <template #header>
        <div class="flex items-center gap-4">
          <el-avatar :size="64" class="bg-primary text-white text-xl">
            {{ authStore.user.username?.charAt(0).toUpperCase() }}
          </el-avatar>
          <div>
            <h2 class="text-xl font-semibold">{{ authStore.user.username }}</h2>
            <p class="text-gray-500 text-sm">{{ authStore.user.email }}</p>
          </div>
        </div>
      </template>

      <div class="space-y-4">
        <div class="flex items-center gap-2">
          <span class="text-gray-500">状态：</span>
          <el-tag :type="authStore.user.status === 1 ? 'success' : 'danger'">
            {{ authStore.user.status === 1 ? '正常' : '禁用' }}
          </el-tag>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500">创建时间：</span>
          <span>{{ formatDate(authStore.user.created_at) }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500">用户ID：</span>
          <span>{{ authStore.user.id }}</span>
        </div>
      </div>
    </el-card>

    <el-card class="mt-6">
      <template #header>
        <h2 class="text-lg font-semibold">快速操作</h2>
      </template>
      <div class="flex gap-4">
        <el-button type="primary">个人设置</el-button>
        <el-button @click="authStore.logout()">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>
