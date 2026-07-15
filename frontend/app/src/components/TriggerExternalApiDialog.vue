<template>
  <q-dialog
    v-model="showDialog"
    style="width: 90%"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @keydown.enter="triggerExtApiIfValid"
  >
    <q-card class="q-pa-sm">
      <q-card-section>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <q-banner dense rounded>
              Provide the date range to synchronise data of the external API, that lie in the past.
            </q-banner>
          </div>
        </div>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <q-banner dense rounded class="bg-orange">
              Please provide the data in UTC format here.
            </q-banner>
          </div>
        </div>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <date-time-picker v-model="beginDate" />
          </div>
        </div>
        <div class="row">
          <div class="col-md-auto">
            <date-time-picker v-model="endDate" />
          </div>
        </div>
      </q-card-section>
      <q-card-actions>
        <q-btn label="Cancel" @click="showDialog = false" color="grey" unelevated />
        <q-space />
        <q-btn
          label="Synchronise"
          :disable="!!validationError"
          @click="triggerExtApi"
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
import type { TriggerSyncExtApiBase } from 'src/services/trigger_external_api_generic/types';
import { useTriggerExternalGenericApiStore } from 'stores/externalApiTriggerStore';
import { date, useQuasar } from 'quasar';

const showDialog = defineModel<boolean | null>({ default: false });
const { ids_to_trigger } = defineProps<{
  ids_to_trigger: Array<number>;
}>();

const store = useTriggerExternalGenericApiStore();
const $q = useQuasar();

const endDate = ref(new Date().toISOString().slice(0, 19).replace('T', ' '));
const beginDate = ref(
  new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10) + ' 00:00:00',
);

const validationError = computed(() => {
  if (!isValidDate(beginDate.value) || !isValidDate(endDate.value))
    return 'Date has an invalid format (YYYY-MM-DD HH:MM:SS).';
  if (new Date(beginDate.value) >= new Date(endDate.value))
    return 'End date must be after begin date.';
  return null;
});

const emit = defineEmits(['success']);
const dateFormat = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
const dateTimeFormat = 'YYYY-MM-DD HH:mm:ss';

function isValidDate(value: string): boolean {
  if (!dateFormat.test(value)) return false;
  const parsed = date.extractDate(value, dateTimeFormat);
  return !Number.isNaN(parsed.getTime()) && date.formatDate(parsed, dateTimeFormat) === value;
}

async function triggerExtApi() {
  if (ids_to_trigger.length === 0) return;

  if (!isValidDate(beginDate.value) || !isValidDate(endDate.value)) {
    $q.notify({
      type: 'negative',
      position: 'top',
      message: 'Please provide valid dates in the format YYYY-MM-DD HH:MM:SS.',
    });
  }
  const data: TriggerSyncExtApiBase = {
    ingest_ids: ids_to_trigger,
    start_date: beginDate.value,
    end_date: endDate.value,
  };
  try {
    await store.dispatchTriggerApi(data);
    $q.notify({
      type: 'positive',
      position: 'top',
      message: 'External API was successfully synced.',
    });
    emit('success');
  } catch {
    $q.notify({
      type: 'negative',
      position: 'top',
      message: 'Failed to synchronise external API.',
    });
  } finally {
    showDialog.value = false;
  }
}

function triggerExtApiIfValid() {
  if (validationError.value) {
    void triggerExtApi();
  }
}
</script>

<style scoped></style>
