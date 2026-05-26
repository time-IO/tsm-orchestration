<template>
  <q-dialog v-model="showDialog" style="width: 90%" @keydown.esc="showDialog = false" @keydown.enter="triggerQCIfValid">
    <q-card class="q-pa-sm">
      <q-card-section>
        <div class="row q-mb-md">
          <div class="col-md-auto">
            <q-banner dense rounded>
              Provide the date range of data that Quality Control Setting should be run on.
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
          @click="triggerQC"
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
import type { TriggerQCSBase } from 'src/services/quality_control_settings_trigger/types';
import { useTriggerQCSStore } from 'stores/qualityControlSettingsTriggerStore';
import { useQuasar } from 'quasar';

const showDialog = defineModel<boolean | null>({ default: false });
const { ids_to_trigger } = defineProps<{
  ids_to_trigger: Array<number>;
}>();

const store = useTriggerQCSStore();
const $q = useQuasar();

const beginDate = ref('2026-01-01 00:00');
const endDate = ref(new Date().toISOString().slice(0, 16).replace('T', ' '));

const beginDateIsAfterEndDate = computed(() => {
  return new Date(beginDate.value) < new Date(endDate.value);
});

const emit = defineEmits(['success']);

async function triggerQC() {
  if (ids_to_trigger.length === 0) return;

  const data: TriggerQCSBase = {
    quality_control_setting_ids: ids_to_trigger,
    start_date: beginDate.value,
    end_date: endDate.value,
  };
  try {
    await store.dispatchTriggerSetting(data);
    $q.notify({
      type: 'positive',
      position: 'top',
      message: 'Successfully synced.',
    });
    emit('success');
  } catch {
    $q.notify({
      type: 'negative',
      position: 'top',
      message: 'Failed to synchronise.',
    });
  } finally {
    showDialog.value = false;
  }
}

function triggerQCIfValid() {
  if (beginDateIsAfterEndDate.value) {
    void triggerQC();
  }
}
</script>

<style scoped></style>
