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

      <q-card-section class="q-pt-sm col column no-wrap" style="min-height: 0">
        <overview-table
          v-model:pagination="pagination"
          :rows="rows"
          :loading="loading"
          :columns="columns"
          storage-key="mqtt-messages"
          :column-widths="columnWidths"
          :column-toggle="false"
          binary-state-sort
          dense
          virtual-scroll
          no-data-label="No messages"
          @request="onRequest"
        >
          <template #toolbar>
            <date-time-picker
              v-model="dateFrom"
              clearable
              dense
              hide-bottom-space
              label="Received after"
              style="width: 230px"
            />
            <date-time-picker
              v-model="dateTo"
              clearable
              dense
              hide-bottom-space
              label="Received before"
              style="width: 230px"
            />
          </template>

          <template #value-append="{ col, row }">
            <copy-button
              v-if="col.name === 'message'"
              :text="row.message"
              size="xs"
              text-color="grey"
            />
          </template>
        </overview-table>
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
import { computed, onUnmounted, ref, watch } from 'vue';
import type { QTableColumn } from 'quasar';
import { useQuasar } from 'quasar';
import CopyButton from '@/components/common/CopyButton.vue';
import OverviewTable from '@/components/common/OverviewTable.vue';
import DateTimePicker from '@/components/DateTimePicker.vue';
import { API } from '@/services';
import { useAuthStore } from '@/stores/authStore';
import { MqttLiveConnection } from '@/services/ingest_mqtt_client';
import type { MqttMessage } from '@/services/ingest_mqtt_messages/types';
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';
import type { ColumnWidths } from '@/utils/overview_table_utils';
import { parseDateTimePickerValue } from '@/utils/time_utils';

const showDialog = defineModel<boolean>({ default: false });
const { ingestId, topic } = defineProps<{
  ingestId: number;
  topic: string;
}>();

const $q = useQuasar();
const authStore = useAuthStore();

const LIVE_REFRESH_DELAY_MS = 1500;
const FILTER_DEBOUNCE_MS = 300;

const initialPagination = (): QTableRequestPropPagination => ({
  sortBy: 'timestamp',
  descending: true,
  page: 1,
  rowsPerPage: 25,
  rowsNumber: 0,
});

const rows = ref<MqttMessage[]>([]);
const loading = ref(false);
const pagination = ref<QTableRequestPropPagination>(initialPagination());
const dateFrom = ref<string | undefined>(undefined);
const dateTo = ref<string | undefined>(undefined);

const status = ref<'connecting' | 'connected' | 'closed' | 'error'>('closed');
const publishSuffix = ref('');
const publishPayload = ref('');

let conn: MqttLiveConnection | null = null;
let requestSeq = 0;
let filterTimer: ReturnType<typeof setTimeout> | undefined;
let liveRefreshTimer: ReturnType<typeof setTimeout> | undefined;

const columnWidths: ColumnWidths = {
  timestamp: { min: 10, default: 12, max: 20 },
  message: { min: 20, default: 48 },
};

const columns: QTableColumn<MqttMessage>[] = [
  {
    name: 'timestamp',
    label: 'Received',
    field: 'timestamp',
    align: 'left',
    sortable: true,
    format: (v: string) => new Date(v).toLocaleString(),
  },
  { name: 'message', label: 'Payload', field: 'message', align: 'left' },
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

const isUsableFilter = (value: string | undefined | null) =>
  !value || parseDateTimePickerValue(value) !== null;

async function loadMessages(requested: QTableRequestPropPagination) {
  const seq = ++requestSeq;
  loading.value = true;
  try {
    const { data } = await API.ingestMqttMessages.fetchMqttMessages(ingestId, {
      datetime_from: parseDateTimePickerValue(dateFrom.value)?.toISOString(),
      datetime_to: parseDateTimePickerValue(dateTo.value)?.toISOString(),
      page_number: requested.page,
      page_size: requested.rowsPerPage,
      order: requested.descending ? 'desc' : 'asc',
    });
    // ignore responses of requests that were superseded meanwhile
    if (seq !== requestSeq) return;
    rows.value = data.mqtt_messages;
    pagination.value = { ...requested, rowsNumber: data.total };
  } catch {
    if (seq === requestSeq) {
      $q.notify({ type: 'negative', message: 'Failed to load MQTT messages' });
    }
  } finally {
    if (seq === requestSeq) loading.value = false;
  }
}

function onRequest({ pagination: requested }: QTableRequestProp) {
  void loadMessages(requested);
}

watch([dateFrom, dateTo], () => {
  if (!showDialog.value || !isUsableFilter(dateFrom.value) || !isUsableFilter(dateTo.value)) {
    return;
  }
  clearTimeout(filterTimer);
  filterTimer = setTimeout(
    () => void loadMessages({ ...pagination.value, page: 1 }),
    FILTER_DEBOUNCE_MS,
  );
});

const liveRefreshRequirementsAreMet = computed(() => {
  const { page, descending } = pagination.value;
  return page === 1 && descending && !dateTo.value;
});

function scheduleLiveRefresh() {
  if (!liveRefreshRequirementsAreMet.value) return;
  clearTimeout(liveRefreshTimer);
  liveRefreshTimer = setTimeout(() => void loadMessages(pagination.value), LIVE_REFRESH_DELAY_MS);
}

function onOpen() {
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
    onMessage: scheduleLiveRefresh,
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
  clearTimeout(filterTimer);
  clearTimeout(liveRefreshTimer);
  conn?.close();
  conn = null;
  status.value = 'closed';
}

function onHide() {
  closeConnection();
  requestSeq++;
  loading.value = false;
  rows.value = [];
  dateFrom.value = undefined;
  dateTo.value = undefined;
  pagination.value = initialPagination();
}

onUnmounted(closeConnection);

function doPublish() {
  if (status.value !== 'connected' || !conn) {
    return;
  }
  conn.publish(publishSuffix.value, publishPayload.value);
}
</script>
