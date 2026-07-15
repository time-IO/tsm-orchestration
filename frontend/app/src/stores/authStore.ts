import { defineStore } from 'pinia';
import type { User } from 'oidc-client-ts';
import { userManager } from 'src/auth/oidcConfig';
import { API } from 'src/services';
import type { UserPublic } from 'src/services/user/types';

/**
 * Prevent multiple event registrations (HMR, multi-import)
 */
let eventsBound = false;

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    userInfo: null as UserPublic | null,
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user && !state.user.expired,
    accessToken: (state) => state.user?.access_token ?? null,
    getUserInfo: (state) => state.user?.profile || null,
    initials(): string | null {
      if (this.isAuthenticated && this.userInfo) {
        const givenName = this.userInfo.given_name;
        const familyName = this.userInfo.family_name;

        if (givenName && familyName) {
          return givenName.charAt(0) + familyName.charAt(0);
        }
      }
      return null;
    },
  },

  actions: {
    async init() {
      this.loading = true;
      try {
        this.user = await userManager.getUser();
      } finally {
        this.loading = false;
      }

      this.bindOidcEvents();
    },

    async fetchUserInfo() {
      try {
        const response = await API.user.getMe();
        this.userInfo = response.data;
      } catch (error) {
        console.error('failed to fetch user information:', error);
        await this.logout();
      }
    },

    login() {
      return userManager.signinRedirect();
    },

    async handleLoginCallback() {
      this.user = await userManager.signinRedirectCallback();
    },

    clearStoredUserAndInfo() {
      this.user = null;
      this.userInfo = null;
    },

    async logout() {
      this.clearStoredUserAndInfo();
      return userManager.signoutRedirect();
    },

    bindOidcEvents() {
      if (eventsBound) return;
      eventsBound = true;

      /**
       * Fired on:
       * - initial login
       * - silent renew
       * - refresh token rotation
       */
      userManager.events.addUserLoaded(async (user) => {
        console.info('OIDC: user loaded / updated');
        this.user = user;
        // Only fetch additional user info if authenticated
        // Only if it is null
        if (this.isAuthenticated && this.userInfo === null) {
          await this.fetchUserInfo();
        }
      });

      /**
       * ~60s before expiration
       */
      userManager.events.addAccessTokenExpiring(() => {
        console.warn('OIDC: token expiring');
      });

      /**
       * Token is no longer usable
       */
      userManager.events.addAccessTokenExpired(() => {
        console.warn('OIDC: token expired');
        this.clearStoredUserAndInfo();
      });

      /**
       * Silent renew failed (network, revoked refresh token, etc.)
       */
      userManager.events.addSilentRenewError((err) => {
        console.error('OIDC: silent renew error', err);
      });

      /**
       * User logged out at the IdP
       */
      userManager.events.addUserSignedOut(() => {
        console.warn('OIDC: user signed out at IdP');
        this.clearStoredUserAndInfo();
      });
    },
  },
});
