<template>
  <q-page class="q-pa-lg">
    <h5>Create a new Data Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest" />
      </div>
    </div>

    <div class="row">
      <div
        class="col-12 col-sm-6 col-lg-3 q-pa-sm"
        style="max-width: 300px"
        v-for="item in data"
        :key="item.name"
      >
        <q-card>
          <q-item style="min-height: 96px; align-items: center">
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
            <q-btn :to="item.path" class="full-width" color="green" icon="add">
              <q-tooltip>Create new Ingest</q-tooltip>
            </q-btn>
          </q-card-actions>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-lg-3 q-pa-sm" style="max-width: 300px">
        <q-card>
          <q-item style="min-height: 96px; align-items: center">
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

                <q-btn
                  v-if="item.docsUrl"
                  round
                  flat
                  icon="help_outline"
                  @click="showDocs(item.docsUrl)"
                  class="text-grey"
                >
                  <q-tooltip> View documentation </q-tooltip>
                </q-btn>

                <q-item-section avatar>
                  <q-btn :to="item.path" square color="green" icon="add">
                    <q-tooltip>Create new Ingest</q-tooltip>
                  </q-btn>
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
    label: 'SFTP/S3',
    description: 'Create a new S3 bucket with SFTP endpoint and parser.',
    path: '/ingest/new/sftp',
  },
  {
    name: 'ext_sftp',
    icon: 'folder_special',
    label: 'External SFTP',
    description:
      'Sync external SFTP folders into a new S3 bucket with a fitting file format and parser',
    path: '/ingest/new/external-sftp',
  },
  {
    name: 'mqtt',
    icon: 'wifi_tethering',
    label: 'MQTT',
    description: 'Create an Ingest topic on the time.IO MQTT broker with a fitting MQTT Parser.',
    path: '/ingest/new/mqtt',
  },
];

const externalAPis = {
  name: 'ext_api',
  icon: 'control_camera',
  label: 'External API',
  description: 'Create a schedule and access credentials for requesting a registered external API.',
  options: [
    {
      name: 'bosch',
      label: 'Bosch IoT',
      path: '/ingest/new/external-api/bosch',
      docsUrl: 'https://bosch-iot-insights.com/ui/pages/api/mongodb-query/latest',
    },
    {
      name: 'dwd',
      label: 'Deutscher Wetterdienst',
      path: '/ingest/new/external-api/dwd',
      docsUrl: 'https://brightsky.dev/docs/#/operations/getWeather',
    },
    {
      name: 'nm',
      label: 'Neutron Monitor',
      path: '/ingest/new/external-api/nm',
      docsUrl: 'https://www.nmdb.eu/nest/help.php#howto',
    },
    { name: 'sensoto', label: 'Sensoto', path: '/ingest/new/external-api/sensoto' },
    { name: 'tsystems', label: 'TSystems', path: '/ingest/new/external-api/tsystems' },
    {
      name: 'ttn',
      label: 'The Things network',
      path: '/ingest/new/external-api/ttn',
      docsUrl: 'https://www.thethingsindustries.com/docs/api/',
    },
    {
      name: 'uba',
      label: 'Umweltbundesamt (UBA) Air Data',
      path: '/ingest/new/external-api/uba',
      docsUrl: 'https://luftdaten.umweltbundesamt.de/api/air-data/v3/doc/',
    },
  ],
};

function showDocs(url: string) {
  window.open(url, '_blank');
}
</script>

<style scoped></style>
