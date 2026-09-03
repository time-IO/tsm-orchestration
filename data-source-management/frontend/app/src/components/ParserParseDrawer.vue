<template>
  <q-drawer
    v-model="drawerIsOpen"
    side="right"
    :width="width"
    :breakpoint="breakpoint"
    bordered
    class="validation-sidebar"
  >
    <div class="validation-sidebar__inner column no-wrap fit">
      <div class="row items-center justify-end q-pt-md q-pr-md">
        <q-btn flat round dense :ripple="false" icon="close" @click="drawerIsOpen = false" />
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
              @update:model-value="handleFileChange"
              :max-file-size="1024 * 1024 * 10"
              :max-files="1"
              @rejected="wasFileRejected = true"
              :error="wasFileRejected"
              error-message="File type is invalid or file is too large"
              hint="Maximum allowed size is 10 MB."
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
              :label="isAlreadyValidated ? 'Validated' : 'Validate'"
              :loading="isValidating"
              :disable="!file || isAlreadyValidated"
              @click="validate"
            />
          </div>
        </div>

        <q-checkbox
          v-model="autoValidate"
          v-if="$q.screen.width >= breakpoint"
          class="q-mt-md q-mb-mt"
          label="Auto-parse when valid changes detected"
        />

        <q-banner
          v-if="!parsingResult.is_valid"
          class="bg-negative text-white q-mt-lg"
          :class="{
            'validation-table--stale': haveSettingsChanged,
          }"
        >
          <template #avatar>
            <q-icon name="error" />
          </template>
          Parsing failed: {{ parsingResult.error }}
        </q-banner>
        <q-banner
          v-if="parsingResult.is_valid && parsingResult.warnings.length > 0"
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
            <li v-for="(warning, index) in parsingResult.warnings" :key="index" class="q-mt-sm">
              {{ warning }}
            </li>
          </ul>
        </q-banner>
        <q-banner
          v-if="parsingResult.is_valid && parsingResult?.data.length"
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
          v-if="parsingResult.is_valid && parsingResult?.data.length"
          class="q-mt-lg validation-sidebar__table-wrap"
          :class="{
            'validation-table--stale': haveSettingsChanged,
          }"
        >
          <q-table
            flat
            bordered
            dense
            :rows="parsingResult?.data"
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
import { fileMetadataIsEqual } from 'src/utils/file_utils';
import { unknownToString } from 'src/utils/string_utils';

const $q = useQuasar();

type ParseAction<T> = (settings: T, file: File) => Promise<ParsingResult>;

const drawerIsOpen = defineModel<boolean>({
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
const wasFileRejected = ref(false);

const isValidating = ref(false);
const parsingResult = ref<ParsingResult>({
  is_valid: true,
  data: [],
  warnings: [],
  error: '',
});

const lastValidatedSettings = ref<T | null>(null);
const lastValidatedFile = ref<File | null>(null);

const autoValidate = ref(false);
let autoValidateTimeout: ReturnType<typeof setTimeout> | null = null;

const tableColumns = computed<QTableColumn[]>(() => {
  const firstRow = parsingResult.value?.data[0];
  if (!firstRow) {
    return [];
  }
  return Object.keys(firstRow).map((key) => ({
    name: key,
    label: key,
    field: key,
    align: 'left',
    format: (value: unknown) => unknownToString(value),
  }));
});

const isAlreadyValidated = computed(() => {
  if (!file.value || !lastValidatedFile.value || !lastValidatedSettings.value) {
    return false;
  }
  return (
    fileMetadataIsEqual(file.value, lastValidatedFile.value) &&
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

function handleFileChange(newFile: File | null) {
  wasFileRejected.value = false;
  file.value = newFile;
  resetResult();

  if (!newFile) {
    lastValidatedFile.value = null;
    lastValidatedSettings.value = null;
  }
}

function resetResult() {
  parsingResult.value.is_valid = true;
  parsingResult.value.data = [];
  parsingResult.value.error = '';
  parsingResult.value.warnings = [];
}

async function validate() {
  if (!file.value) {
    return;
  }
  isValidating.value = true;

  parsingResult.value = await props.parseAction(props.parsingSettings, file.value);

  lastValidatedSettings.value = structuredClone(toRaw(props.parsingSettings));
  lastValidatedFile.value = file.value;
  isValidating.value = false;
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
  overflow: hidden;
  min-height: 0;
  flex: 0 1 auto;
}

.validation-sidebar__table-wrap :deep(.q-table__container) {
  max-height: 100%;
}

.validation-table--stale {
  opacity: 0.4;
}
</style>
