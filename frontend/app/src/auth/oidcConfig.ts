import { UserManager, WebStorageStateStore } from 'oidc-client-ts';

const oidcConfig = {
  authority: process.env.OIDC_IDP_URL!,
  client_id: process.env.OIDC_CLIENT_ID!,
  redirect_uri: process.env.OIDC_REDIRECT_URI!,
  response_type: 'code',
  scope: process.env.OIDC_SCOPE!,
  post_logout_redirect_uri: process.env.OIDC_POST_LOGOUT_REDIRECT_URI!,
  automaticSilentRenew: true,
  includeIdTokenInSilentRenew: true,
  userStore: new WebStorageStateStore({ store: window.localStorage }),
};

export const userManager = new UserManager(oidcConfig);
