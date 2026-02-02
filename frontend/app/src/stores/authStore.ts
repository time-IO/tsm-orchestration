import {defineStore} from "pinia";
import {User} from "oidc-client-ts";
import {userManager} from "src/auth/oidcConfig";


/**
 * Prevent multiple event registrations (HMR, multi-import)
 */
let eventsBound = false;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user && !state.user.expired,
    accessToken: (state) => state.user?.access_token ?? null,
    getUserInfo: (state) => state.user?.profile || null,
    initials: (state) => {
      if (state.isAuthenticated) {
        const givenName = state.getUserInfo.given_name
        const familyName = state.getUserInfo.family_name

        if (
          givenName != null && givenName.length > 0 &&
          familyName != null && familyName.length > 0
        ) {
          return givenName[0] + familyName[0]
        }

        if (state.getUserInfo.name.length > 2) {
          return state.getUserInfo.name[0] + state.getUserInfo.name[1]
        }
      }
      return null
    }
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

    login() {
      return userManager.signinRedirect();
    },

    async handleLoginCallback() {
      this.user = await userManager.signinRedirectCallback();
    },

    async logout() {
      this.user = null;
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
      userManager.events.addUserLoaded((user) => {
        console.info("OIDC: user loaded / updated");
        console.log("NEW TOKEN", user.access_token);
        this.user = user;
      });

      /**
       * ~60s before expiration
       */
      userManager.events.addAccessTokenExpiring(() => {
        console.warn("OIDC: token expiring");
      });

      /**
       * Token is no longer usable
       */
      userManager.events.addAccessTokenExpired(() => {
        console.warn("OIDC: token expired");
        this.user = null;
      });

      /**
       * Silent renew failed (network, revoked refresh token, etc.)
       */
      userManager.events.addSilentRenewError((err) => {
        console.error("OIDC: silent renew error", err);
      });

      /**
       * User logged out at the IdP
       */
      userManager.events.addUserSignedOut(() => {
        console.warn("OIDC: user signed out at IdP");
        this.user = null;
      });
    }
  },
});
