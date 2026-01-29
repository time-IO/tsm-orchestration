import { User, UserManager, WebStorageStateStore } from 'oidc-client-ts'
import { environment } from './environment'
import {useAuthStore} from "stores/authStore";


export default class AuthService {
  userManager: UserManager
  store

  constructor () {
    const settings = {
      authority: process.env.authorityUrl,
      client_id: process.env.clientId,
      redirect_uri: process.env.redirectUri,
      response_type: 'code',
      scope: process.env.clientScope,
      userStore: new WebStorageStateStore(),
      loadUserInfo: true,
      automaticSilentRenew: true
    }
    this.userManager = new UserManager(settings)
    this.store = useAuthStore()
  }
  public async init(){
    const user = await this.getUser()
    // todo check token expired
    this.store.setUpUserCredentials(user)

  }

  get loggedIn():boolean {
    return this.store.loggedIn
  }

  get user(): Record<string, unknown> | null {
    return this.store.user
  }

  reset(){
    this.store.setUpUserCredentials(null)
  }

  public signInRedirect () {
    return this.userManager.signinRedirect()
  }

  public signInCallback () {
    return this.userManager.signinCallback()
  }

  public logout (): Promise<void> {
    // return this.userManager.signoutRedirect() // hifis does not support this
    this.reset()
    return this.userManager.removeUser()
  }

  public getUser (): Promise<User | null> {
    return this.userManager.getUser()
  }

  public async refreshToken(){
    const user: User| null = await this.userManager.signinSilent()
    this.store.setUpUserCredentials(user)
  }
}
