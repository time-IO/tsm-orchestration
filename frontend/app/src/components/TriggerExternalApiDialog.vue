<template>
  <q-dialog v-model="showDialog" style="width: 90%">
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
          :disable="!beginDateIsAfterEndDate"
          @click="triggerExtApi"
          color="primary"
        >
          <q-tooltip v-if="!beginDateIsAfterEndDate"> End date must be after begin date </q-tooltip>
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
import { useQuasar } from 'quasar';

const showDialog = defineModel<boolean | null>({ default: false });
const { provider, ids_to_trigger } = defineProps<{
  provider: string;
  ids_to_trigger: Array<number>;
}>();

const store = useTriggerExternalGenericApiStore();
const $q = useQuasar();

const beginDate = ref('2026-01-01 00:00');
const endDate = ref(new Date().toISOString().slice(0, 16).replace('T', ' '));

const beginDateIsAfterEndDate = computed(() => {
  return new Date(beginDate.value) < new Date(endDate.value);
});

const emit = defineEmits(['success']);

async function triggerExtApi() {
  if (ids_to_trigger.length === 0) return;

  const data: TriggerSyncExtApiBase = {
    ingest_ids: ids_to_trigger,
    start_date: beginDate.value,
    end_date: endDate.value,
  };
  try {
    await store.dispatchTriggerApi(provider, data);
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
</script>

<style scoped></style>
