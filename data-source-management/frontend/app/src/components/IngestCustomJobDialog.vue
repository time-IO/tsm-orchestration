<template>
  <q-dialog v-model="showDialog" backdrop-filter="blur(4px) saturate(150%)" @show="init">
    <q-card style="width: 520px; max-width: 90vw">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">{{ job ? 'Edit custom job' : 'Add custom job' }}</div>
        <q-space />
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>

      <q-form class="q-gutter-md" @submit.prevent="save">
        <q-card-section class="q-gutter-md">
          <q-select
            v-model="jobType"
            :options="specs"
            option-value="job_type"
            option-label="label"
            emit-value
            map-options
            outlined
            label="Job type"
            :disable="!!job"
            :rules="[rules.REQUIRED]"
            :hint="spec?.description"
            @update:model-value="resetParams"
          />

          <q-input
            v-model="cron"
            outlined
            label="Cron expression"
            hint="Five fields: minute hour day-of-month month day-of-week, in UTC, e.g. 0 3 * * 0"
            :rules="[rules.REQUIRED, cronRule]"
          />

          <q-input
            v-for="p in spec?.params ?? []"
            :key="p.name"
            v-model.number="params[p.name]"
            type="number"
            outlined
            :label="p.label"
            :min="p.minimum"
            :max="p.maximum"
            :rules="[rules.REQUIRED, rules.INTEGER, ruleFactories.MIN(p.minimum), ruleFactories.MAX(p.maximum)]"
          />

          <q-input
            v-model.number="jitter"
            type="number"
            outlined
            label="Start delay (seconds)"
            hint="0 to 59, chosen randomly if empty"
            :rules="[jitterRule]"
          />

          <q-input v-model="note" outlined label="Note" maxlength="200" />

          <q-toggle v-model="enabled" label="Enabled" />
        </q-card-section>

        <q-card-actions align="right" class="q-pa-md">
          <q-btn v-close-popup flat label="Cancel" />
          <q-btn type="submit" color="primary" label="Save" :loading="isSaving" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { API } from '@/services';
import { ruleFactories, rules } from '@/utils/validation/rules';
import type { CustomJob, CustomJobInput, CustomJobSpec } from '@/services/ingest_schedule/types';

const { ingestId, job = null } = defineProps<{ ingestId: number; job?: CustomJob | null }>();
const emit = defineEmits<{ saved: [] }>();
const showDialog = defineModel<boolean>({ default: false });

const $q = useQuasar();

const specs = ref<CustomJobSpec[]>([]);
const jobType = ref<string | null>(null);
const cron = ref('');
const params = ref<Record<string, number>>({});
const jitter = ref<number | null>(null);
const note = ref('');
const enabled = ref(true);
const isSaving = ref(false);

const spec = computed(() => specs.value.find((s) => s.job_type === jobType.value));

const FIELD = /^[0-9*,/-]+$/;

function cronRule(val: string): true | string {
  const fields = val.trim().split(/\s+/);
  if (fields.length === 5 && fields.every((f) => FIELD.test(f))) return true;
  return "5 fields of numbers, '*', ',', '-' and '/'";
}

function jitterRule(val: number | null | string): true | string {
  if (val === null || val === '') return true;
  const n = Number(val);
  return Number.isInteger(n) && n >= 0 && n <= 59 ? true : 'Integer between 0 and 59';
}

function resetParams() {
  params.value = Object.fromEntries((spec.value?.params ?? []).map((p) => [p.name, p.default]));
}

async function init() {
  try {
    specs.value = await API.ingestSchedule.getAvailableCustomJobs(ingestId);
  } catch {
    specs.value = [];
    $q.notify({ type: 'negative', position: 'top', message: 'Could not load the job types.' });
  }
  jobType.value = job?.job_type ?? specs.value[0]?.job_type ?? null;
  cron.value = job?.cron_expression ?? '';
  jitter.value = job?.jitter_seconds ?? null;
  note.value = job?.note ?? '';
  enabled.value = job?.enabled ?? true;
  resetParams();
  if (job) params.value = { ...params.value, ...(job.params as Record<string, number>) };
}

async function save() {
  isSaving.value = true;
  const input: CustomJobInput = {
    cron_expression: cron.value.trim(),
    jitter_seconds: jitter.value === null || String(jitter.value) === '' ? null : jitter.value,
    enabled: enabled.value,
    params: params.value,
    note: note.value || null,
  };
  try {
    if (job) {
      await API.ingestSchedule.updateCustomJob(ingestId, job.id, input);
    } else {
      await API.ingestSchedule.createCustomJob(ingestId, { ...input, job_type: jobType.value! });
    }
    emit('saved');
    showDialog.value = false;
  } catch {
    $q.notify({ type: 'negative', position: 'top', message: 'Failed to save the custom job.' });
  } finally {
    isSaving.value = false;
  }
}
</script>
