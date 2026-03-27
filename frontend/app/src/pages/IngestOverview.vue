<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Data Ingest</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" :label="t('newIngest')" to="/ingest/new" />
    </div>

    <div class="row">
      <div class="col-3 q-pa-sm" v-for="item in data" :key="item.name">
        <q-card>
          <q-item>
            <q-item-section avatar>
              <q-avatar :icon="item.icon" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption> {{ item.description }} </q-item-label>
            </q-item-section>
          </q-item>
          <q-separator />
          <q-card-actions>
            <q-space />
            <q-btn :to="item.path" class="full-width" color="primary">Show</q-btn>
          </q-card-actions>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();

const data = [
  {
    name: 'sftp',
    icon: 'folder_copy',
    label: 'SFTP',
    description: 'some description for sftp',
    path: '/ingest/sftp',
  },
  {
    name: 'ext_sftp',
    icon: 'folder_special',
    label: 'External SFTP',
    description: 'some description for ext_sftp',
    path: '/ingest/external-sftp',
  },
  {
    name: 'mqtt',
    icon: 'wifi_tethering',
    label: 'MQTT',
    description: 'some description for mqtt',
    path: '/ingest/mqtt',
  },
  {
    name: 'ext_api',
    icon: 'control_camera',
    label: 'External API',
    description: 'some description for sftp',
    path: '/ingest/external-api',
  },
];
</script>

<style scoped></style>
