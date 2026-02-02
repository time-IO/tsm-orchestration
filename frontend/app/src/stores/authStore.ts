import {acceptHMRUpdate, defineStore} from 'pinia'
import {ref, computed} from 'vue'
import {User, UserManager} from 'oidc-client-ts'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isLoading: false,
    error: null
  }),

  getters: {
    hasToken: (state) => !!state.user?.access_token,
    getUserInfo: (state) => state.user?.profile || null,
    isAuthenticated: (state) => !!state.user
  },

  actions: {
    async initialize() {
      try {
        this.isLoading = true

        const config = {
          authority: 'http://localhost:8080/keycloak/realms/local-dev',
          client_id: 'dev-client',
          redirect_uri: 'http://localhost:3000/login-callback',
          response_type: 'code',
          scope: 'openid profile eduperson_principal_name eduperson_entitlement eduperson_unique_id email offline_access',
          post_logout_redirect_uri: 'http://localhost:3000',
          silent_redirect_uri: 'http://localhost:3000/silent-renew',
          automaticSilentRenew: true,
          includeIdTokenInSilentRenew: true
        }

        this.userManager = new UserManager(config)

        const user = await this.userManager.getUser()
        if (user) {
          this.setUser(user)
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    setUser(user) {
      this.user = user
    },

    async login() {
      try {
        this.isLoading = true
        await this.userManager.signinRedirect()
      } catch (error) {
        console.error('Login error:', error)
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    async handleCallback() {
      try {
        this.isLoading = true
        const user = await this.userManager.signinCallback()
        this.setUser(user)
        return user
      } catch (error) {
        console.error('Callback error:', error)
        this.error = error.message
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async logout() {
      try {
        this.isLoading = true
        await this.userManager.signoutRedirect()
      } catch (error) {
        console.error('Logout error:', error)
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    async handleSignoutCallback() {
      try {
        this.isLoading = true
        await this.userManager.signoutCallback()
        this.setUser(null)
      } catch (error) {
        console.error('Signout callback error:', error)
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    async getAccessToken() {
      if (!this.user) return null

      try {
        return await this.userManager.getAccessToken()
      } catch (error) {
        console.error('Token retrieval error:', error)
        return null
      }
    },

    // Navigation helper methods
    // async navigateAfterLogin() {
    //   const router = useRouter()
    //   router.push('/')
    // },
    //
    // async navigateAfterLogout() {
    //   const router = useRouter()
    //   router.push('/login')
    // }
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}
