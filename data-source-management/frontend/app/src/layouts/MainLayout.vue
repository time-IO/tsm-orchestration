<template>
  <q-layout view="lHh lpR lff">
    <q-header elevated>
      <q-toolbar class="bg-blue-grey-5 text-white">
        <q-btn
          v-if="authStore.isAuthenticated"
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>{{ t('appname') }}</q-toolbar-title>

        <q-btn round flat>
          <q-avatar>
            <span v-if="authStore.isAuthenticated">{{ authStore.initials }}</span>
            <q-icon v-else name="account_circle" />
          </q-avatar>
          <q-tooltip>Account</q-tooltip>
          <q-menu>
            <q-list style="min-width: 100px">
              <template v-if="authStore.isAuthenticated">
                <q-item @click="handleLogout" clickable v-close-popup>
                  <q-item-section>Logout</q-item-section>
                </q-item>
              </template>
              <template v-else>
                <q-item @click="handleLogin" clickable v-close-popup>
                  <q-item-section>Login</q-item-section>
                </q-item>
              </template>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-if="authStore.isAuthenticated" v-model="leftDrawerOpen" show-if-above bordered>
      <q-item to="/">
        <q-item-section avatar>
          <q-icon name="home" size="xs" />
        </q-item-section>
        <q-item-section class="text-uppercase"> Home </q-item-section>
      </q-item>
      <q-separator />
      <q-list>
        <q-item
          v-for="item in topNavigation"
          :key="item.name"
          :to="item.route"
          class="relative-position"
          @mouseenter="item.addOptions ? openMenu(item.name) : undefined"
          @mouseleave="item.addOptions ? scheduleClose() : undefined"
        >
          <q-item-section v-if="item.icon" avatar>
            <q-icon :name="item.icon" size="xs" />
          </q-item-section>
          <q-item-section class="text-uppercase">
            {{ item.name }}
          </q-item-section>
          <q-item-section
            v-if="(item.addRoute || item.addOptions) && authStore.isAuthenticated"
            side
          >
            <q-btn
              flat
              round
              dense
              icon="add"
              size="xs"
              color="grey-6"
              :title="'Add ' + item.name"
              @click.prevent.stop="item.addRoute ? router.push(item.addRoute) : undefined"
            />
          </q-item-section>

          <!-- Menu anchored to the q-item itself, not the button -->
          <q-menu
            v-if="item.addOptions"
            :model-value="hoveredMenuName === item.name"
            no-parent-event
            no-focus
            :auto-close="false"
            anchor="top end"
            self="top start"
            :offset="[0, 0]"
            transition-show="jump-right"
            transition-hide="jump-left"
            @update:model-value="
              (val: boolean) => {
                if (!val) closeMenu();
              }
            "
            @mouseenter="cancelClose()"
            @mouseleave="scheduleClose()"
          >
            <q-list class="bg-white submenu-list" style="min-width: 240px">
              <template v-for="(opt, i) in item.addOptions" :key="i">
                <template v-if="'separator' in opt">
                  <q-separator />
                  <q-item-label
                    v-if="opt.label"
                    header
                    class="text-grey-6"
                    style="font-size: 0.75rem; padding: 6px 12px"
                  >
                    {{ opt.label }}
                  </q-item-label>
                </template>
                <q-item
                  v-else
                  clickable
                  v-ripple
                  @click="
                    router.push(opt.route);
                    closeMenu();
                  "
                >
                  <q-item-section>{{ opt.label }}</q-item-section>
                </q-item>
              </template>
            </q-list>
          </q-menu>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <div :class="{ 'page-width-constrained': route.meta.constrainWidth }">
        <router-view />
      </div>
    </q-page-container>
    <the-footer />
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from 'stores/authStore';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import TheFooter from 'components/TheFooter.vue';

const { t } = useI18n();
const leftDrawerOpen = ref(false);

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const $q = useQuasar();

const handleLogin = async () => {
  try {
    await authStore.login();
  } catch {
    $q.notify({
      type: 'negative',
      position: 'top',
      timeout: 0,
      actions: [
        {
          icon: 'close',
          color: 'white',
          round: true,
          handler: () => {},
        },
      ],
      message: 'Authorization provider not reachable. Please contact an application admin.',
    });
  }
};

const handleLogout = async () => {
  try {
    await authStore.logout();
  } catch (e) {
    console.error(e);
  } finally {
    await router.push('/');
  }
};

interface NavOptionItem {
  label: string;
  route: string;
}
interface NavSeparatorItem {
  separator: true;
  label?: string;
}
interface NavEntry {
  name: string;
  route: string;
  icon: string;
  addRoute?: string;
  addOptions?: Array<NavOptionItem | NavSeparatorItem>;
}

const topNavigation: NavEntry[] = [
  {
    name: 'Ingest',
    route: '/ingest',
    icon: 'input',
    addRoute: '/ingest/new',
    addOptions: [
      { label: 'SFTP/S3', route: '/ingest/new/sftp' },
      { label: 'External SFTP', route: '/ingest/new/external-sftp' },
      { label: 'MQTT', route: '/ingest/new/mqtt' },
      { label: 'External MQTT', route: '/ingest/new/external-mqtt' },
      { label: 'HTTP', route: '/ingest/new/http' },
      { separator: true, label: 'External API' },
      { label: 'Bosch IoT', route: '/ingest/new/external-api/bosch' },
      { label: 'Deutscher Wetterdienst', route: '/ingest/new/external-api/dwd' },
      { label: 'Neutron Monitor', route: '/ingest/new/external-api/nm' },
      { label: 'Sensoto', route: '/ingest/new/external-api/sensoto' },
      { label: 'TSystems', route: '/ingest/new/external-api/tsystems' },
      { label: 'The Things Network', route: '/ingest/new/external-api/ttn' },
      { label: 'Umweltbundesamt (UBA)', route: '/ingest/new/external-api/uba' },
    ],
  },
  {
    name: 'Parser',
    route: '/parser',
    icon: 'difference',
    addRoute: '/parser/new',
    addOptions: [
      { label: 'CSV', route: '/parser/new/csv' },
      { label: 'JSON', route: '/parser/new/json' },
      { label: 'SOILCAN', route: '/parser/new/soilcan' },
    ],
  },
  {
    name: 'Quality Control',
    route: '/quality-control',
    icon: 'verified',
    addRoute: '/quality-control/new',
  },
  {
    name: 'Trigger External Api',
    route: '/trigger/external-api',
    icon: 'sync',
  },
];

const hoveredMenuName = ref<string | null>(null);
let closeTimer: ReturnType<typeof setTimeout> | null = null;
let openTimer: ReturnType<typeof setTimeout> | null = null;

function openMenu(name: string) {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
  if (openTimer) return; // already scheduled
  openTimer = setTimeout(() => {
    hoveredMenuName.value = name;
    openTimer = null;
  }, 500);
}

function scheduleClose() {
  if (openTimer) {
    clearTimeout(openTimer);
    openTimer = null;
  }
  closeTimer = setTimeout(() => {
    hoveredMenuName.value = null;
    closeTimer = null;
  }, 150);
}

function cancelClose() {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}

function closeMenu() {
  hoveredMenuName.value = null;
}

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}
</script>

<style scoped>
.page-width-constrained {
  max-width: 1400px;
  width: 100%;
}
</style>
