import { acceptHMRUpdate, defineStore } from 'pinia'
import { User } from 'oidc-client-ts'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  const access_token = computed(() => user.value?.access_token ?? '')

  const id_token = computed(() => user.value?.id_token ?? '')

  const loggedIn = computed(() => !!user.value)

  const setUpUserCredentials = (userSetup: User|null) => {
    user.value = userSetup
  }

  const clearUserSession = () => {
    user.value = null
  }

  return {
    user,
    access_token,
    id_token,
    loggedIn,
    setUpUserCredentials,
    clearUserSession
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}
