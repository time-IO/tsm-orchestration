<template>
  <q-layout view="lHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer"/>

        <q-toolbar-title>{{ t('appname') }}</q-toolbar-title>

        <q-btn round flat>
          <q-avatar>
            <span v-if="authStore.isAuthenticated">{{ authStore.initials }}</span>
            <q-icon v-else name="account_circle"/>
          </q-avatar>
          <q-tooltip>Account</q-tooltip>
          <q-menu>
            <q-list style="min-width: 100px">
              <template v-if="authStore.isAuthenticated">
                <q-item
                  @click="handleLogout"
                  clickable v-close-popup>
                  <q-item-section>Logout</q-item-section>
                </q-item>
                <q-separator/>
                <q-item clickable v-close-popup>
                  <q-item-section>Settings</q-item-section>
                </q-item>
                <q-separator/>
                <q-item clickable v-close-popup>
                  <q-item-section>Help &amp; Feedback</q-item-section>
                </q-item>
              </template>
              <template v-else>
                <q-item
                  @click="handleLogin"
                  clickable v-close-popup>
                  <q-item-section>Login</q-item-section>
                </q-item>
              </template>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-item to="/">
        <q-item-section avatar>
          <q-icon name="home" size="xs"/>
        </q-item-section>
        <q-item-section class="text-uppercase" data-cy="SidebarMenu_ItemLabel">
          Home
        </q-item-section>
      </q-item>
      <q-separator/>
      <q-list>
        <q-item v-for="item in topNavigation" :key="item.name" :to="item.route">
          <q-item-section v-if="item.icon" avatar>
            <q-icon :name="item.icon" size="xs"/>
          </q-item-section>
          <q-item-section class="text-uppercase" data-cy="SidebarMenu_ItemLabel">
            {{ item.name }}
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view/>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import {ref} from 'vue';
import {useI18n} from 'vue-i18n';
import {useAuthStore} from "stores/authStore";
import {useRouter} from "vue-router";

const {t} = useI18n()
const leftDrawerOpen = ref(false);


const authStore = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  await authStore.login()
}

const handleLogout = async () => {
  await authStore.logout()
  await router.push('/')
}

const topNavigation = [
  {
    name: 'Ingest',
    route: '/ingest',
    icon: 'input',
  },
  {
    name: 'Parser',
    route: '/parser',
    icon: 'difference',
  },
  {
    name: 'Quality Control',
    route: '/quality-control',
    icon: 'verified',
  },
];

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>
