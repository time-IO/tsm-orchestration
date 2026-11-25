<template>
  <q-dialog
    v-model="showDialog"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @show="onOpen"
    @hide="onHide"
  >
    <q-card class="q-pa-sm column no-wrap" style="width: 60vw; max-width: 80vw; height: 80vh">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">MQTT Client</div>
        <q-badge :color="statusColor" class="q-ml-md" :label="statusLabel" text-color="white" />
        <q-space />
        <div class="text-caption text-grey-7 q-mr-sm">{{ topic }}/#</div>
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>

      <q-card-section class="row items-center q-gutter-sm q-pb-none">
        <div class="text-caption text-grey-7">
          {{ messages.length }} message{{ messages.length === 1 ? '' : 's' }}
          <span v-if="dropped > 0" class="text-orange-9">· {{ dropped }} dropped</span>
        </div>
        <q-space />
        <q-btn
          dense
          flat
          icon="delete_sweep"
          label="Clear"
          :disable="!messages.length"
          @click="messages = []"
        />
      </q-card-section>

      <q-card-section class="q-pt-sm col column no-wrap" style="min-height: 0">
        <overview-table
          v-model:pagination="pagination"
          :rows="messages"
          :loading="false"
          :columns="columns"
          storage-key="mqtt-messages"
          :column-widths="columnWidths"
          :column-toggle="false"
          row-key="key"
          dense
          virtual-scroll
          :no-data-label="status === 'connected' ? 'Waiting for messages…' : 'Not connected'"
        />
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="text-subtitle2 text-weight-medium q-mb-sm">Publish a test message</div>
        <div class="row q-col-gutter-md items-start">
          <div class="col-12 col-md-6">
            <q-input
              v-model="publishSuffix"
              dense
              outlined
              label="Topic"
              :prefix="`${topic}/`"
              hint="Sub-topic under this ingest (leave empty for the base topic)"
            />
          </div>
          <div class="col-12 col-md-6">
            <q-input
              v-model="publishPayload"
              dense
              outlined
              type="textarea"
              autogrow
              label="Payload"
            />
          </div>
        </div>
        <div class="row items-center q-mt-sm">
          <q-space />
          <q-btn
            color="primary"
            icon="publish"
            label="Publish"
            :disable="status !== 'connected'"
            @click="doPublish"
          />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue';
import type { QTableColumn } from 'quasar';
import { useQuasar } from 'quasar';
import OverviewTable from '@/components/common/OverviewTable.vue';
import { useAuthStore } from '@/stores/authStore';
import { MqttLiveConnection } from '@/services/ingest_mqtt_client';
import type { MqttLiveMessage } from '@/services/ingest_mqtt_client/types';
import type { QTableRequestPropPagination } from '@/services/types';
import type { ColumnWidths } from '@/utils/overview_table_utils';

const showDialog = defineModel<boolean>({ default: false });
const { ingestId, topic } = defineProps<{
  ingestId: number;
  topic: string;
}>();

const $q = useQuasar();
const authStore = useAuthStore();

type Row = MqttLiveMessage & { key: string; time: string };

const MAX_ROWS = 500;
const messages = ref<Row[]>([]);
const dropped = ref(0);
const status = ref<'connecting' | 'connected' | 'closed' | 'error'>('closed');
const publishSuffix = ref('');
const publishPayload = ref('');

let conn: MqttLiveConnection | null = null;
let seq = 0;

const pagination = ref<QTableRequestPropPagination>({
  sortBy: '',
  descending: false,
  page: 1,
  rowsPerPage: 25,
});

const columnWidths: ColumnWidths = {
  time: { min: 8, default: 10, max: 16 },
  topic: { min: 10, default: 20 },
  payload: { min: 20, default: 40 },
};

const columns: QTableColumn<Row>[] = [
  { name: 'time', label: 'Received', field: 'time', align: 'left' },
  { name: 'topic', label: 'Topic', field: 'topic', align: 'left' },
  { name: 'payload', label: 'Payload', field: 'payload', align: 'left' },
];

const statusLabel = computed(
  () =>
    ({
      connecting: 'Connecting…',
      connected: 'Connected',
      closed: 'Disconnected',
      error: 'Error',
    })[status.value],
);
const statusColor = computed(
  () =>
    ({ connecting: 'orange', connected: 'positive', closed: 'grey', error: 'negative' })[
      status.value
    ],
);

function onOpen() {
  messages.value = [];
  dropped.value = 0;
  status.value = 'connecting';
  const token = authStore.accessToken;
  if (!token) {
    status.value = 'error';
    $q.notify({ type: 'negative', message: 'Not authenticated' });
    return;
  }
  conn = new MqttLiveConnection(ingestId, token, {
    onConnected: () => {
      status.value = 'connected';
    },
    onMessage: (m) => {
      messages.value.unshift({
        ...m,
        key: `${Date.now()}-${seq++}`,
        // No explicit hour12: let each locale pick its own convention
        // (en-US → am/pm, most of Europe → 24h).
        time: new Date(m.received_at).toLocaleTimeString(),
      });
      if (messages.value.length > MAX_ROWS) {
        messages.value.length = MAX_ROWS;
      }
    },
    onDropped: (count) => {
      dropped.value = count;
    },
    onPublished: () => {
      $q.notify({ type: 'positive', message: 'Message published', timeout: 800 });
    },
    onError: (detail) => {
      status.value = 'error';
      $q.notify({ type: 'negative', message: detail });
    },
    onClose: () => {
      if (status.value !== 'error') {
        status.value = 'closed';
      }
    },
  });
  conn.connect();
}

function closeConnection() {
  conn?.close();
  conn = null;
  status.value = 'closed';
}

function onHide() {
  closeConnection();
}

onUnmounted(closeConnection);

function doPublish() {
  if (status.value !== 'connected' || !conn) {
    return;
  }
  conn.publish(publishSuffix.value, publishPayload.value);
}
</script>
