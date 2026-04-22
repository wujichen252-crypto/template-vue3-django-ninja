<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElForm, ElFormItem, ElInput, ElButton, ElMessage, ElCard } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const registerForm = reactive({
  username: '',
  password: '',
  email: ''
})

const loading = ref(false)

async function handleRegister() {
  if (!registerForm.username || !registerForm.password || !registerForm.email) {
    ElMessage.warning('请填写所有字段')
    return
  }

  loading.value = true
  try {
    await authStore.register(registerForm.username, registerForm.password, registerForm.email)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    ElMessage.error('注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <el-card class="w-full max-w-md">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold text-black">注册</h1>
          <p class="text-gray-500 mt-2">创建新账号</p>
        </div>
      </template>

      <el-form :model="registerForm" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱"
            type="email"
            size="large"
            prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="w-full"
            :loading="loading"
            native-type="submit"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="text-center mt-4">
        <span class="text-gray-500 text-sm">已有账号？</span>
        <router-link to="/login" class="text-primary hover:underline ml-1">登录</router-link>
      </div>
    </el-card>
  </div>
</template>
