<template>
  <q-dialog
    v-model="showDialog"
    style="width: 90%"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @keydown.enter="triggerSftpIfValid"
  >
    <q-card class="q-pa-sm">
      <q-card-section>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <q-banner dense rounded>
              Optionally provide a date range (by file modification time) to restrict the external
              SFTP synchronisation. Leave a field empty to omit that bound; leave both empty to sync
              all files.
            </q-banner>
          </div>
        </div>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <q-banner dense rounded class="bg-orange">
              Please provide the dates in UTC format here.
            </q-banner>
          </div>
        </div>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <date-time-picker v-model="beginDate" label="Start date (optional)" clearable />
          </div>
        </div>
        <div class="row">
          <div class="col-md-auto">
            <date-time-picker v-model="endDate" label="End date (optional)" clearable />
          </div>
        </div>
      </q-card-section>
      <q-card-actions>
        <q-btn label="Cancel" @click="showDialog = false" color="grey" unelevated />
        <q-space />
        <q-btn
          label="Synchronise"
          :disable="!!validationError || submitting"
          :loading="submitting"
          @click="triggerSftp"
          color="primary"
        >
          <q-tooltip v-if="validationError">{{ validationError }}</q-tooltip>
        </q-btn>
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import DateTimePicker from 'components/DateTimePicker.vue';
import { computed, ref } from 'vue';
import type { TriggerSyncExtSftpBase } from 'src/services/trigger_external_sftp/types';
import { useTriggerExternalSftpStore } from 'stores/externalSftpTriggerStore';
import { date, useQuasar } from 'quasar';

const showDialog = defineModel<boolean | null>({ default: false });
const { ingest_id } = defineProps<{
  ingest_id: number;
}>();

const store = useTriggerExternalSftpStore();
const $q = useQuasar();

const beginDate = ref<string | undefined>('');
const endDate = ref<string | undefined>('');
const submitting = ref(false);

const emit = defineEmits(['success']);
const dateFormat = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
const dateTimeFormat = 'YYYY-MM-DD HH:mm:ss';

function isValidDate(value: string): boolean {
  if (!dateFormat.test(value)) return false;
  const parsed = date.extractDate(value, dateTimeFormat);
  return !Number.isNaN(parsed.getTime()) && date.formatDate(parsed, dateTimeFormat) === value;
}

const validationError = computed(() => {
  if (beginDate.value && !isValidDate(beginDate.value))
    return 'Start date has an invalid format (YYYY-MM-DD HH:MM:SS).';
  if (endDate.value && !isValidDate(endDate.value))
    return 'End date has an invalid format (YYYY-MM-DD HH:MM:SS).';
  if (beginDate.value && endDate.value && new Date(beginDate.value) >= new Date(endDate.value))
    return 'End date must be after start date.';
  return null;
});

async function triggerSftp() {
  if (validationError.value || submitting.value) return;

  const data: TriggerSyncExtSftpBase = {
    ingest_id,
    ...(beginDate.value ? { start_date: beginDate.value } : {}),
    ...(endDate.value ? { end_date: endDate.value } : {}),
  };
  submitting.value = true;
  try {
    await store.dispatchTriggerSftp(data);
    $q.notify({
      type: 'positive',
      position: 'top',
      message: 'External SFTP sync was successfully triggered.',
    });
    emit('success');
  } catch {
    $q.notify({
      type: 'negative',
      position: 'top',
      message: 'Failed to trigger external SFTP sync.',
    });
  } finally {
    submitting.value = false;
    showDialog.value = false;
  }
}

function triggerSftpIfValid() {
  if (!validationError.value) {
    void triggerSftp();
  }
}
</script>

<style scoped></style>
