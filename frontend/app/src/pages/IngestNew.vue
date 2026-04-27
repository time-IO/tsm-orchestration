<template>
  <q-page class="q-pa-lg">
    <h5>Create a new data ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest" />
      </div>
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
            <q-btn :to="item.path" class="full-width" color="green">Create</q-btn>
          </q-card-actions>
        </q-card>
      </div>

      <div class="col-3 q-pa-sm">
        <q-card>
          <q-item>
            <q-item-section avatar>
              <q-avatar :icon="externalAPis.icon" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ externalAPis.label }}</q-item-label>
              <q-item-label caption> {{ externalAPis.description }} </q-item-label>
            </q-item-section>
          </q-item>
          <q-separator />
          <q-list>
            <template v-for="item in externalAPis.options" :key="item.name">
              <q-item>
                <q-item-section>
                  <q-item-label>{{ item.label }}</q-item-label>
                </q-item-section>
                <q-item-section avatar>
                  <q-btn :to="item.path" square color="green" icon="add" />
                </q-item-section>
              </q-item>
              <q-separator />
            </template>
          </q-list>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
const data = [
  {
    name: 'sftp',
    icon: 'folder_copy',
    label: 'SFTP',
    description: 'some description for sftp',
    path: '/ingest/new/sftp',
  },
  {
    name: 'ext_sftp',
    icon: 'folder_special',
    label: 'External SFTP',
    description: 'some description for ext_sftp',
    path: '/ingest/new/external-sftp',
  },
  {
    name: 'mqtt',
    icon: 'wifi_tethering',
    label: 'MQTT',
    description: 'some description for mqtt',
    path: '/ingest/new/mqtt',
  },
];

const externalAPis = {
  name: 'ext_api',
  icon: 'control_camera',
  label: 'External API',
  description: 'some description for sftp',
  options: [
    { name: 'bosch', label: 'Bosch IoT', path: '/ingest/new/external-api/bosch' },
    { name: 'dwd', label: 'Deutscher Wetterdienst', path: '/ingest/new/external-api/dwd' },
    { name: 'nm', label: 'Neutron Monitor', path: '/ingest/new/external-api/nm' },
    { name: 'tsystems', label: 'TSystems', path: '/ingest/new/external-api/tsystems' },
    { name: 'ttn', label: 'The Things network', path: '/ingest/new/external-api/ttn' },
    { name: 'uba', label: 'Umweltbundesamt (UBA) Air Data', path: '/ingest/new/external-api/uba' },
  ],
};
</script>

<style scoped></style>
