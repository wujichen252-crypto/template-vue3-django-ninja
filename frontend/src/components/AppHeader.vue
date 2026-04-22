<script setup lang="ts">
import { ref } from 'vue'
import { ElDropdown, ElDropdownMenu, ElDropdownItem, ElAvatar } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<template>
  <div class="flex items-center gap-4">
    <span class="text-gray-600 text-sm">{{ authStore.user?.username || '未登录' }}</span>
    <el-dropdown @command="handleCommand">
      <el-avatar :size="32" class="cursor-pointer bg-primary text-white">
        {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
      </el-avatar>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">个人中心</el-dropdown-item>
          <el-dropdown-item command="settings">设置</el-dropdown-item>
          <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>
