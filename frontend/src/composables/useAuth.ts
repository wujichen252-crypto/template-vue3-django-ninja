import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()

  const isLoggedIn = computed(() => !!authStore.token)
  const currentUser = computed(() => authStore.user)

  async function login(username: string, password: string) {
    return await authStore.login({ username, password })
  }

  async function register(username: string, password: string, email: string) {
    return await authStore.register({ username, password, email })
  }

  function logout() {
    authStore.logout()
  }

  return {
    isLoggedIn,
    currentUser,
    login,
    register,
    logout
  }
}
