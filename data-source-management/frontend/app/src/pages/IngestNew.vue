<template>
  <q-page class="q-pa-lg">
    <h5>Create a new Data Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest" />
      </div>
    </div>

    <div class="clusters">
      <IngestOptionCluster
        v-for="cluster in clusters"
        :key="cluster.name"
        v-model:selected-variant="selectedVariant"
        :cluster="cluster"
        :variants="externalApis"
        @help="helpOption = $event"
        @create="createIngest"
        @docs="showDocs"
      />
    </div>

    <IngestOptionHelpDialog
      :option="helpOption"
      :icon="helpCluster?.icon"
      :source-label="helpOption?.variantSelect ? selectedVariant?.label : undefined"
      @close="helpOption = null"
    />
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import IngestOptionCluster from '@/components/IngestOptionCluster.vue';
import IngestOptionHelpDialog from '@/components/IngestOptionHelpDialog.vue';
import type { IngestVariant, IngestCluster, IngestOption } from '@/components/ingestOptions';

const clusters: IngestCluster[] = [
  {
    name: 'files',
    icon: 'folder_copy',
    label: 'File transfer (SFTP / S3)',
    description:
      'Data arrives as files. time.IO keeps the raw files in an object storage bucket and parses them with a file parser.',
    items: [
      {
        name: 'sftp',
        label: 'SFTP/S3',
        description: 'Upload files to a time.IO bucket.',
        flow: 'sftp',
        path: '/ingest/new/sftp',
        helpText:
          'Your data logger or a script uploads data files to a storage area that time.IO provides for you. You receive login details for SFTP and S3. time.IO keeps every uploaded file and automatically imports the measurements from it, using the file parser you select.',
        chooseIf: [
          'your logger or software writes data files, e.g. CSV',
          'you or a script can upload these files regularly',
          'you want to keep the original files next to the imported data',
        ],
      },
      {
        name: 'ext_sftp',
        label: 'External FTP/SFTP',
        description: 'time.IO syncs files from your server on a schedule.',
        flow: 'ext_sftp',
        path: '/ingest/new/external-sftp',
        helpText:
          'Your data files are already collected on your own FTP or SFTP server. time.IO connects to it at a fixed interval, copies new files, keeps them and imports the measurements.',
        chooseIf: [
          'your data files already arrive on an FTP or SFTP server you operate',
          'you do not want to change where your logger sends its data',
          'a delay of up to one sync interval is acceptable',
        ],
      },
    ],
  },
  {
    name: 'mqtt',
    icon: 'wifi_tethering',
    label: 'MQTT',
    description:
      'Data arrives as messages as soon as it is measured. Each message is parsed with an MQTT parser.',
    items: [
      {
        name: 'mqtt',
        label: 'MQTT',
        description: 'Publish to a topic on the time.IO broker.',
        flow: 'mqtt',
        path: '/ingest/new/mqtt',
        helpText:
          'Your device sends each measurement as a message to the time.IO MQTT broker as soon as it is measured. time.IO imports every message right away.',
        chooseIf: [
          'your device can send data via MQTT',
          'you want to see new data almost in real time',
          'your device sends many small messages rather than files',
        ],
      },
      {
        name: 'ext_mqtt',
        label: 'External MQTT',
        description: 'time.IO subscribes to a topic on your broker.',
        flow: 'ext_mqtt',
        path: '/ingest/new/external-mqtt',
        helpText:
          'Your devices already send messages to your own MQTT broker. time.IO subscribes to a topic on that broker and imports every message it receives.',
        chooseIf: [
          'you already run your own MQTT broker',
          'your devices should keep sending to it unchanged',
          'you want to see new data almost in real time',
        ],
      },
    ],
  },
  {
    name: 'http',
    icon: 'http',
    label: 'HTTP',
    description:
      'Data arrives over the web: send files to time.IO, or let time.IO request a supported web API.',
    items: [
      {
        name: 'http',
        label: 'HTTP',
        description: 'POST files to a time.IO endpoint.',
        flow: 'http',
        path: '/ingest/new/http',
        helpText:
          'Your device or software sends data files to a time.IO web address. time.IO keeps every file and automatically imports the measurements from it.',
        chooseIf: [
          'your device or software can send web (HTTP) requests, but not SFTP or MQTT',
          'only standard web connections are allowed in your network',
          'you want to keep the original files next to the imported data',
        ],
      },
      {
        name: 'ext_api',
        label: 'External API',
        description: 'time.IO requests a registered API on a schedule.',
        flow: 'ext_api',
        variantSelect: true,
        helpText:
          'Your data is available from a supported online service, e.g. a weather service or the cloud of a device manufacturer. time.IO requests new data from it at a fixed interval and imports it. Select the service from the list.',
        chooseIf: [
          'your data is available from one of the supported services',
          'you have the access credentials the service requires',
          'a delay of up to one sync interval is acceptable',
        ],
      },
    ],
  },
];

const externalApis: IngestVariant[] = [
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
  { name: 'zentra', label: 'Zentra', path: '/ingest/new/external-api/zentra' },
];

const router = useRouter();

const selectedVariant = ref<IngestVariant | null>(null);
const helpOption = ref<IngestOption | null>(null);
/** The cluster of the ingest whose help is open; its icon heads the dialog. */
const helpCluster = computed(() =>
  clusters.find((cluster) => cluster.items.some((item) => item.name === helpOption.value?.name)),
);

function createIngest(option: IngestOption, variant: IngestVariant | null) {
  const path = option.variantSelect ? variant?.path : option.path;
  if (path) void router.push(path);
}

function showDocs(variant: IngestVariant) {
  if (variant.docsUrl) window.open(variant.docsUrl, '_blank');
}
</script>

<style scoped lang="scss">
.clusters {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 24px;
}

// Large screens (Quasar lg, 1440px): three clusters side by side. Each cluster
// shares the grid rows via subgrid (see IngestOptionCluster), so the headers align.
@media (min-width: 1440px) {
  .clusters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    row-gap: 0;
  }
}
</style>
