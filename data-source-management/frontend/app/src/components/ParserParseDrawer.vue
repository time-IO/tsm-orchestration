<template>
  <q-drawer
    v-model="isOpen"
    side="right"
    :width="width"
    :breakpoint="breakpoint"
    bordered
    class="validation-sidebar"
  >
    <div class="validation-sidebar__inner column no-wrap fit">
      <div class="row items-center justify-end q-pt-md q-pr-md">
        <q-btn flat round dense :ripple="false" icon="close" @click="isOpen = false" />
      </div>
      <div class="col column no-wrap q-px-md q-pb-md validation-sidebar__body">
        <div class="text-caption text-grey q-mb-sm">
          Parse a file with current settings of this {{ parserType }} parser.
        </div>
        <div class="row items-stretch q-col-gutter-md">
          <div class="col">
            <q-file
              v-model="file"
              filled
              :label="`${allowedFileTypeName} file`"
              :accept="allowedFileType"
              clearable
              :disable="isValidating"
              :loading="isFileLoading"
              @update:model-value="handleFileChange"
            >
              <template #prepend>
                <q-icon name="upload_file" />
              </template>
            </q-file>
          </div>
          <div class="col-auto">
            <q-btn
              class="full-height"
              unelevated
              color="primary"
              label="Validate"
              icon="check"
              :loading="isValidating"
              :disable="!file || isAlreadyValidated"
              @click="validate"
            />
          </div>
        </div>
        <q-checkbox
          v-model="autoValidate"
          class="q-mt-md q-mb-mt"
          label="Auto-parse when valid changes detected"
        />
        <q-banner
          v-if="validationResult === false"
          class="bg-negative text-white q-mt-lg"
          :class="{
            'validation-table--stale': haveSettingsChanged,
          }"
        >
          <template #avatar>
            <q-icon name="error" />
          </template>
          Parsing failed: {{ validationError }}
        </q-banner>
        <q-banner
          v-if="validationResult === true && validationWarnings.length > 0"
          class="bg-warning text-black q-mt-lg"
          :class="{
            'validation-table--stale': haveSettingsChanged,
          }"
        >
          <template #avatar>
            <q-icon name="warning" />
          </template>
          <div class="text-weight-bold q-mt-sm">Parsing finished with warnings</div>
          <ul>
            <li v-for="(warning, index) in validationWarnings" :key="index" class="q-mt-sm">
              {{ warning }}
            </li>
          </ul>
        </q-banner>
        <q-banner
          v-if="validationResult === true && validationData.length"
          class="bg-positive text-white q-mt-lg"
          :class="{
            'validation-table--stale': haveSettingsChanged,
          }"
        >
          <template #avatar>
            <q-icon name="check_circle" />
          </template>
          Parsing succeeded.
        </q-banner>
        <div
          v-if="validationResult === true && validationData.length"
          class="col q-mt-lg validation-sidebar__table-wrap"
          :class="{
            'validation-table--stale': haveSettingsChanged,
          }"
        >
          <q-table
            flat
            bordered
            :rows="validationData"
            :columns="tableColumns"
            row-key="__row"
            :pagination="{ rowsPerPage: 10 }"
            :rows-per-page-options="[10, 25, 50, 0]"
            wrap-cells
            separator="cell"
          />
        </div>
      </div>
    </div>
  </q-drawer>
</template>
<script setup lang="ts" generic="T extends ParserPayloadParse">
import { computed, ref, toRaw, watch } from 'vue';
import { useQuasar } from 'quasar';
import type { QTableColumn } from 'quasar';
import type { ParserPayloadParse, ParsingResult } from 'src/services/types';
const $q = useQuasar();
type ParseAction<T> = (settings: T, file: File) => Promise<ParsingResult>;
const isOpen = defineModel<boolean>({
  default: false,
});
const props = defineProps<{
  parsingSettings: T;
  parseAction: ParseAction<T>;
  allowedFileType: string;
  allowedFileTypeName: string;
  parserType: string;
}>();
const breakpoint = computed(() => $q.screen.sizes.md);
const width = computed(() => $q.screen.width * ($q.screen.width < breakpoint.value ? 0.8 : 0.4));
const file = ref<File | null>(null);
const isFileLoading = ref(false);
const isValidating = ref(false);
const validationData = ref<Record<string, unknown>[]>([]);
const validationError = ref('');
const validationWarnings = ref<string[]>([]);
const validationResult = ref<boolean | null>(null);
const lastValidatedSettings = ref<T | null>(null);
const lastValidatedFile = ref<File | null>(null);
const autoValidate = ref(true);
let autoValidateTimeout: ReturnType<typeof setTimeout> | null = null;
const tableColumns = computed<QTableColumn[]>(() => {
  const firstRow = validationData.value[0];
  if (!firstRow) {
    return [];
  }
  return Object.keys(firstRow).map((key) => ({
    name: key,
    label: key,
    field: key,
    align: 'left',
    format: (value: unknown) => formatValue(value),
  }));
});
const isAlreadyValidated = computed(() => {
  if (!file.value || !lastValidatedFile.value || !lastValidatedSettings.value) {
    return false;
  }
  return (
    filesAreEqual(file.value, lastValidatedFile.value) &&
    settingsAreEqual(props.parsingSettings, lastValidatedSettings.value)
  );
});
const haveSettingsChanged = computed(() => {
  if (!lastValidatedSettings.value) {
    return false;
  }
  return !settingsAreEqual(props.parsingSettings, lastValidatedSettings.value);
});
watch(
  () => props.parsingSettings,
  () => {
    if (!autoValidate.value || !file.value || isValidating.value) {
      return;
    }
    if (autoValidateTimeout) {
      clearTimeout(autoValidateTimeout);
    }
    autoValidateTimeout = setTimeout(() => {
      if (autoValidate.value && file.value && haveSettingsChanged.value) {
        void validate();
      }
    }, 1000);
  },
  { deep: true },
);
function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  if (typeof value !== 'string') {
    // eslint-disable-next-line @typescript-eslint/no-base-to-string
    return String(value);
  }
  const date = new Date(value);
  if (!Number.isNaN(date.getTime()) && isIsoDate(value)) {
    return new Intl.DateTimeFormat('de-DE', {
      dateStyle: 'medium',
      timeStyle: 'medium',
    }).format(date);
  }
  return value;
}
// TODO: move to utils
function isIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value);
}
function handleFileChange(newFile: File | null) {
  isFileLoading.value = true;
  file.value = newFile;
  resetResult();
  if (!newFile) {
    lastValidatedFile.value = null;
    lastValidatedSettings.value = null;
  }
  setTimeout(() => {
    isFileLoading.value = false;
  }, 150);
}
function resetResult() {
  validationResult.value = null;
  validationData.value = [];
  validationError.value = '';
  validationWarnings.value = [];
}
async function validate() {
  if (!file.value) {
    return;
  }
  isValidating.value = true;
  try {
    const result: ParsingResult = await props.parseAction(props.parsingSettings, file.value);
    validationResult.value = result.is_valid;
    validationData.value = result.data;
    validationError.value = result.error;
    validationWarnings.value = result.warnings;
    lastValidatedSettings.value = structuredClone(toRaw(props.parsingSettings));
    lastValidatedFile.value = file.value;
  } catch (e) {
    console.error('Validation failed', e);
    validationResult.value = null;
    validationData.value = [];
    validationError.value = 'Error';
    validationWarnings.value = [];
  } finally {
    isValidating.value = false;
  }
}
function filesAreEqual(a: File, b: File): boolean {
  return (
    a.name === b.name && a.size === b.size && a.lastModified === b.lastModified && a.type === b.type
  );
}
function settingsAreEqual(a: T, b: T): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
</script>
<style scoped>
.validation-sidebar__inner {
  height: 100%;
}

.validation-sidebar__body {
  overflow: hidden;
}

.validation-sidebar__table-wrap {
  overflow: auto;
  min-height: 0;
  padding-bottom: 10vh;
}

.validation-table--stale {
  opacity: 0.4;
}
</style>
