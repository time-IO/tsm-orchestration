<template>
  <q-dialog
    v-model="showDialog"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @show="loadEntries"
    @hide="onHide"
  >
    <q-card class="q-pa-sm column no-wrap" style="width: 70vw; max-width: 90vw; max-height: 80vh">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Journal</div>
        <q-space />
        <div class="text-caption text-grey-7 q-mr-sm">User-facing logs for this ingest</div>
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>

      <q-card-section class="row items-end q-col-gutter-md q-pb-none">
        <div class="col-12 col-sm-4">
          <q-select
            v-model="level"
            dense
            outlined
            clearable
            emit-value
            map-options
            label="Level"
            :options="levelOptions"
            @update:model-value="loadEntries"
          />
        </div>
        <div class="col-6 col-sm-3">
          <q-input
            v-model.number="limit"
            dense
            outlined
            type="number"
            label="Limit"
            min="1"
            @keyup.enter="loadEntries"
          />
        </div>
        <div class="col-6 col-sm-5 row items-center">
          <q-space />
          <q-btn
            dense
            flat
            icon="refresh"
            label="Refresh"
            :loading="isLoading"
            @click="loadEntries"
          />
        </div>
      </q-card-section>

      <q-card-section class="q-pt-sm col scroll" style="min-height: 0">
        <q-table
          flat
          bordered
          dense
          :rows="entries"
          :columns="columns"
          row-key="id"
          :loading="isLoading"
          :pagination="{ rowsPerPage: 15 }"
          no-data-label="No journal entries"
        >
          <template #body-cell-level="props">
            <q-td :props="props">
              <q-badge :color="levelColor(props.row.level)" :label="props.row.level" />
            </q-td>
          </template>
          <template #body-cell-message="props">
            <q-td :props="props">
              <div class="journal-message">{{ props.row.message }}</div>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { QTableColumn } from 'quasar';
import { useQuasar } from 'quasar';
import { API } from 'src/services';
import type { JournalEntry } from 'src/services/ingest_journal/types';

const showDialog = defineModel<boolean>({ default: false });
const { ingestId } = defineProps<{
  ingestId: number;
}>();

const $q = useQuasar();

const entries = ref<JournalEntry[]>([]);
const isLoading = ref(false);
const level = ref<string | null>(null);
const limit = ref<number>(100);

const levelOptions = [
  { label: 'Info', value: 'INFO' },
  { label: 'Warning', value: 'WARNING' },
  { label: 'Error', value: 'ERROR' },
];

const columns: QTableColumn<JournalEntry>[] = [
  {
    name: 'timestamp',
    label: 'Timestamp',
    field: 'timestamp',
    align: 'left',
    format: (v: string) => new Date(v).toLocaleString(),
    sortable: true,
  },
  { name: 'level', label: 'Level', field: 'level', align: 'left', sortable: true },
  { name: 'origin', label: 'Origin', field: 'origin', align: 'left', sortable: true },
  { name: 'message', label: 'Message', field: 'message', align: 'left' },
];

function levelColor(lvl: string): string {
  switch ((lvl || '').toUpperCase()) {
    case 'ERROR':
      return 'negative';
    case 'WARNING':
      return 'orange';
    case 'INFO':
      return 'primary';
    default:
      return 'grey';
  }
}

async function loadEntries() {
  isLoading.value = true;
  try {
    const response = await API.ingestJournal.fetchJournal(ingestId, {
      ...(level.value ? { level: level.value } : {}),
      ...(limit.value ? { limit: limit.value } : {}),
    });
    entries.value = response.data.journal_entries;
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to load journal entries' });
  } finally {
    isLoading.value = false;
  }
}

function onHide() {
  entries.value = [];
}
</script>

<style scoped>
.journal-message {
  max-width: 40vw;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
