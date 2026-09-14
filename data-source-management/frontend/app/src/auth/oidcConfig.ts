import { UserManager, WebStorageStateStore } from 'oidc-client-ts';

const oidcConfig = {
  authority: import.meta.env.OIDC_IDP_URL!,
  client_id: import.meta.env.OIDC_CLIENT_ID!,
  redirect_uri: import.meta.env.OIDC_REDIRECT_URI!,
  response_type: 'code',
  scope: import.meta.env.OIDC_SCOPE!,
  post_logout_redirect_uri: import.meta.env.OIDC_POST_LOGOUT_REDIRECT_URI!,
  automaticSilentRenew: true,
  includeIdTokenInSilentRenew: true,
  userStore: new WebStorageStateStore({ store: window.localStorage }),
};

export const userManager = new UserManager(oidcConfig);
