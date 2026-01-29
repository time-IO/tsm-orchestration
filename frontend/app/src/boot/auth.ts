import {defineBoot} from "#q-app/wrappers";
import AuthService from "src/services/authService";


export default defineBoot(async ({ app }) => {

  const $auth = new AuthService()

  // todo not sure if really needed (maybe for page refresh...)
  await $auth.init()

  app.config.globalProperties.$auth = $auth;

});
