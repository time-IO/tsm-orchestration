<template>
  <q-dialog
    v-model="showDialog"
    style="width: 90%"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
  >
    <q-card class="q-pa-sm" style="min-width: 480px">
      <q-card-section>
        <q-banner dense rounded class="q-mb-md">
          Parse the files of this ingest again. By default only files that are not yet parsed
          successfully are processed. The date range refers to the upload time of the files.
          Leave a field empty to omit it.
        </q-banner>
        <q-banner dense rounded class="bg-orange q-mb-md">
          Please provide the dates in UTC format here.
        </q-banner>

        <div class="q-mb-md">
          <date-time-picker v-model="beginDate" label="Start date (optional)" clearable />
        </div>
        <div class="q-mb-md">
          <date-time-picker v-model="endDate" label="End date (optional)" clearable />
        </div>

        <q-input
          v-model="filenamePattern"
          label="Filename pattern (optional)"
          hint="Matched against the full file path including folders, e.g. *.csv or data/*.csv"
          filled
          clearable
          class="q-mb-md"
        />

        <q-toggle
          v-model="includeParsed"
          label="Also reparse files that are already parsed"
          class="q-mb-sm"
        />

        <q-option-group
          v-if="includeParsed && !useSpecificParser"
          v-model="parsedFilesParser"
          type="radio"
          :options="parsedFilesParserOptions"
          class="q-mb-md"
        />

        <q-toggle
          v-model="useSpecificParser"
          label="Use one specific parser for all files"
          class="q-mb-sm"
        />

        <parser-select-by-type
          v-if="useSpecificParser"
          v-model="parserId"
          :permission-group-id="permissionGroupId"
          :disable="!permissionGroupId"
          class="q-mb-md"
        />
      </q-card-section>

      <q-card-actions>
        <q-btn label="Cancel" @click="showDialog = false" color="grey" unelevated />
        <q-space />
        <q-btn
          label="Reparse"
          :disable="!!validationError || submitting"
          :loading="submitting"
          @click="triggerReparse"
          color="primary"
        >
          <q-tooltip v-if="validationError">{{ validationError }}</q-tooltip>
        </q-btn>
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>


<script setup lang="ts">
import DateTimePicker from '@/components/DateTimePicker.vue';
import ParserSelectByType from '@/components/ParserSelectByType.vue';
import { computed, ref, watch } from 'vue';
import type { TriggerReparseBase } from '@/services/trigger_reparse/types';
import { useTriggerReparseStore } from '@/stores/reparseTriggerStore';
import { date, useQuasar } from 'quasar';

const showDialog = defineModel<boolean | null>({ default: false });
const { ingest_id, permissionGroupId = null } = defineProps<{
  ingest_id: number;
  permissionGroupId?: number | null | undefined;
}>();

const store = useTriggerReparseStore();
const $q = useQuasar();

const beginDate = ref<string | undefined>('');
const endDate = ref<string | undefined>('');
const filenamePattern = ref<string | null>('');
const includeParsed = ref(false);
const parsedFilesParser = ref<'current' | 'original'>('current');
const useSpecificParser = ref(false);
const parserId = ref<number | null | undefined>(null);
const submitting = ref(false);

watch(useSpecificParser, (enabled) => {
  if (!enabled) parserId.value = null;
});

const emit = defineEmits(['success']);
const dateFormat = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
const dateTimeFormat = 'YYYY-MM-DD HH:mm:ss';

const parsedFilesParserOptions = [
  { label: 'Current parser of this ingest', value: 'current' },
  {
    label: 'Parser used originally (files whose parser no longer exists are skipped)',
    value: 'original',
  },
];

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
  if (useSpecificParser.value && !parserId.value) return 'Please select a parser.';
  return null;
});

async function triggerReparse() {
  if (validationError.value || submitting.value) return;

  const data: TriggerReparseBase = {
    ingest_id,
    include_parsed: includeParsed.value,
    parsed_files_parser:
      includeParsed.value && !useSpecificParser.value ? parsedFilesParser.value : 'current',
    ...(beginDate.value ? { start_date: beginDate.value} : {}),
    ...(endDate.value ? {end_date: endDate.value} : {}),
    ...(filenamePattern.value ? { filename_pattern: filenamePattern.value } : {}),
    ...(useSpecificParser.value && parserId.value ? { parser_id: parserId.value } : {}),
  };
  submitting.value = true;
  try {
    await store.dispatchTriggerReparse(data);
    $q.notify({
      type: 'positive',
      position: 'top',
      message: 'Reparsing was successfully triggered. See the journal for the result.',
    });
    emit('success');
  } catch (error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data
      ?.detail;
    $q.notify({
      type: 'negative',
      position: 'top',
      message:
        typeof detail === 'string'
          ? `Failed to trigger reparsing: ${detail}`
          : 'Failed to trigger reparsing.',
    });
  } finally {
    submitting.value = false;
    showDialog.value = false;
  }
}
</script>
