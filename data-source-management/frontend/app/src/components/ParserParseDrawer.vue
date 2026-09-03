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

        <parser-parse-file-input
          v-model:file="file"
          v-model:was-file-rejected="wasFileRejected"
          :is-validating="isValidating"
          :is-already-validated="isAlreadyValidated"
          :allowed-file-type="allowedFileType"
          :allowed-file-type-name="allowedFileTypeName"
          @change="handleFileChange"
          @validate="validate"
        />

        <q-checkbox
          v-model="autoValidate"
          v-if="$q.screen.width >= breakpoint"
          class="q-mt-md q-mb-mt"
          label="Auto-parse when valid changes detected"
        />

        <parser-parse-banner :parsing-result="parsingResult" :have-settings-changed="haveSettingsChanged" />

        <parser-parse-result-table
          v-if="parsingResult.is_valid && parsingResult.data.length"
          class="q-mt-lg"
          :data="parsingResult.data"
          :is-stale="haveSettingsChanged"
        />
      </div>
    </div>
  </q-drawer>
</template>

<script setup lang="ts" generic="T extends ParserPayloadParse">
import { computed, ref, toRaw, watch } from 'vue';
import { useQuasar } from 'quasar';
import type { ParserPayloadParse, ParsingResult } from 'src/services/types';
import { fileMetadataIsEqual } from 'src/utils/file_utils';
import ParserParseFileInput from 'components/ParserParseFileInput.vue';
import ParserParseBanner from 'components/ParserParseBanner.vue';
import ParserParseResultTable from 'components/ParserParseResultTable.vue';

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
    if (!autoValidate.value || !file.value) {
      return;
    }
    if (autoValidateTimeout) {
      clearTimeout(autoValidateTimeout);
    }
    autoValidateTimeout = setTimeout(() => {
      triggerAutoValidateIfDue();
    }, 1000);
  },
  { deep: true },
);

function triggerAutoValidateIfDue() {
  if (!autoValidate.value || !file.value || isValidating.value || !haveSettingsChanged.value) {
    return;
  }
  void validate();
}

function handleFileChange(newFile: File | null) {
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

  const settingsForThisRequest = structuredClone(toRaw(props.parsingSettings));
  const fileForThisRequest = file.value;

  parsingResult.value = await props.parseAction(settingsForThisRequest, fileForThisRequest);

  lastValidatedSettings.value = settingsForThisRequest;
  lastValidatedFile.value = fileForThisRequest;
  isValidating.value = false;

  triggerAutoValidateIfDue();
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
</style>
