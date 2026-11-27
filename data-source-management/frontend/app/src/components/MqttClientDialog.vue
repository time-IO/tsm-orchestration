<template>
  <q-dialog
    v-model="showDialog"
    :maximized="$q.screen.lt.md"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @show="onOpen"
    @hide="onHide"
  >
    <q-card
      class="q-pa-sm column no-wrap"
      :style="$q.screen.lt.md ? undefined : 'width: 60vw; max-width: 80vw; height: 80vh'"
    >
      <q-card-section class="row no-wrap items-center q-pb-none">
        <div class="text-h6 ellipsis" style="min-width: 0">Message History</div>
        <q-btn
          class="q-ml-md no-wrap"
          style="flex-shrink: 0"
          :outline="!isLive"
          :unelevated="isLive"
          :color="isLive ? 'negative' : 'grey-7'"
          icon="fiber_manual_record"
          label="Live"
          size="sm"
          dense
          padding="2px 8px"
          @click="enableLive"
        >
          <q-tooltip>
            {{
              isLive
                ? 'New messages appear automatically'
                : 'Click to show the newest messages automatically'
            }}
          </q-tooltip>
        </q-btn>
        <q-space />
        <q-btn
          class="q-ml-sm q-mr-sm no-pointer-events"
          style="flex-shrink: 0"
          unelevated
          :color="statusColor"
          :label="statusLabel"
          size="sm"
          dense
          padding="2px 8px"
          :ripple="false"
          tabindex="-1"
        />
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>

      <q-card-section class="q-pt-sm col column no-wrap mqtt-messages" style="min-height: 0">
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
          @cell-click="onCellClick"
        >
          <template #toolbar>
            <div class="col row items-center mqtt-toolbar">
              <date-time-picker
                v-model="dateFrom"
                clearable
                dense
                hide-bottom-space
                label="Received after"
                class="mqtt-filter"
              />
              <date-time-picker
                v-model="dateTo"
                clearable
                dense
                hide-bottom-space
                label="Received before"
                class="mqtt-filter"
              />
            </div>
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

      <q-card-section class="q-pt-none">
        <q-card flat>
          <q-card-section class="q-pa-none">
            <div class="row items-center q-mb-sm">
              <div class="text-h6">Publish a test message</div>
            </div>
            <q-input
              v-model="publishPayload"
              class="mqtt-payload-input"
              outlined
              type="textarea"
              rows="4"
              label="Payload"
            />
            <div class="row q-col-gutter-x-md q-col-gutter-y-sm items-start q-pt-md">
              <div class="col-12 col-md row no-wrap items-start">
                <div class="mqtt-topic-prefix" :title="`${topic}/`">{{ topic }}/</div>
                <q-input
                  v-model="publishSuffix"
                  class="col mqtt-topic-suffix"
                  dense
                  outlined
                  placeholder="Sub-topic"
                  hint="Leave empty to publish to the base topic"
                />
              </div>
              <div class="col-12 col-md-auto row justify-end">
                <q-btn
                  color="primary"
                  icon="publish"
                  label="Publish"
                  style="height: 40px"
                  :disable="status !== 'connected'"
                  @click="doPublish"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </q-card-section>
    </q-card>

    <json-content-dialog
      v-model="payloadDialogOpen"
      title="Payload"
      :subtitle="selectedMessage ? new Date(selectedMessage.timestamp).toLocaleString() : undefined"
      :content="selectedMessage?.message ?? null"
    />
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import type { QTableColumn } from 'quasar';
import { useQuasar } from 'quasar';
import CopyButton from '@/components/common/CopyButton.vue';
import JsonContentDialog from '@/components/common/JsonContentDialog.vue';
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
const selectedMessage = ref<MqttMessage | null>(null);
const payloadDialogOpen = ref(false);
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
  {
    name: 'message',
    label: 'Payload',
    field: 'message',
    align: 'left',
    classes: 'mqtt-payload cursor-pointer',
  },
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

const isLive = computed(() => status.value === 'connected' && liveRefreshRequirementsAreMet.value);

function onCellClick(colName: string, row: MqttMessage) {
  if (colName !== 'message') return;
  selectedMessage.value = row;
  payloadDialogOpen.value = true;
}

function enableLive() {
  if (isLive.value) return;
  if (status.value === 'closed' || status.value === 'error') {
    closeConnection();
    onOpen();
  }
  pagination.value = { ...pagination.value, page: 1, sortBy: 'timestamp', descending: true };
  if (dateTo.value) {
    dateTo.value = undefined;
  } else {
    void loadMessages(pagination.value);
  }
}

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

<style scoped>
.mqtt-messages :deep(td.mqtt-payload),
.mqtt-payload-input :deep(textarea) {
  font-family: monospace;
}

.mqtt-toolbar {
  gap: 8px;
}

.mqtt-filter {
  flex: 1 1 200px;
  max-width: 260px;
}

.mqtt-topic-prefix {
  min-width: 0;
  height: 40px;
  line-height: 38px;
  padding: 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  border: 1px solid rgba(0, 0, 0, 0.24);
  border-right: none;
  border-radius: 4px 0 0 4px;
  background-color: #f5f5f5;
  color: rgba(0, 0, 0, 0.6);
  white-space: nowrap;
}

.mqtt-topic-suffix {
  min-width: 140px;
}

.mqtt-topic-suffix :deep(.q-field__control),
.mqtt-topic-suffix :deep(.q-field__control::before),
.mqtt-topic-suffix :deep(.q-field__control::after) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}
</style>
