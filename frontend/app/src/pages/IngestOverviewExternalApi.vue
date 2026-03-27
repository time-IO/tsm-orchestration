<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Ingest - External Api</h5>
    <q-card-actions class="q-pa-none">
      <q-btn label="back" icon="chevron_left" to="/ingest" />
    </q-card-actions>

    <div class="row">
      <div class="col-3 q-pa-sm" v-for="item in data" :key="item.name">
        <q-card>
          <q-item>
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
const data = [
  { name: 'bosch', label: 'Bosch IoT', path: '/ingest/external-api/bosch', description: 'lorem ipsum' },
  { name: 'dwd', label: 'Deutscher Wetterdienst', path: '/ingest/external-api/dwd', description: 'lorem ipsum' },
  { name: 'nm', label: 'Neutron Monitor', path: '/ingest/external-api/nm', description: 'lorem ipsum' },
  { name: 'tsystems', label: 'TSystems', path: '/ingest/external-api/tsystems', description: 'lorem ipsum' },
  { name: 'ttn', label: 'The Things network', path: '/ingest/external-api/ttn', description: 'lorem ipsum' },
  { name: 'uba', label: 'Umweltbundesamt (UBA) Air Data', path: '/ingest/external-api/uba', description: 'lorem ipsum' },
];
</script>

<style scoped></style>
