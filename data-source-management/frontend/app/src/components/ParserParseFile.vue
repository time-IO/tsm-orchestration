<template>
  <q-dialog v-model="isOpen">
    <q-card style="width: 1000px; max-width: 90vw">
      <q-card-section>
        <div class="text-h6">Validate {{ parserType }} parser</div>
      </q-card-section>

      <q-card-section>
        <q-file
          v-model="file"
          filled
          :label="`${allowedFileTypeName} file`"
          :accept="allowedFileType"
          clearable
          :disable="isValidating"
          @update:model-value="resetResult"
        >
          <template #prepend>
            <q-icon name="upload_file"/>
          </template>
        </q-file>

        <div
          v-if="file"
          class="text-caption text-grey q-mt-sm"
        >
          Selected file: {{ file.name }}
        </div>

        <q-banner
          v-if="validationResult === false"
          class="bg-negative text-white q-mt-lg"
        >
          <template #avatar>
            <q-icon name="error"/>
          </template>

          Parsing failed: {{ validationError }}
        </q-banner>

        <q-banner
          v-if="validationResult === true && validationWarnings.length > 0"
          class="bg-warning text-black q-mt-lg"
        >
          <template #avatar>
            <q-icon name="warning"/>
          </template>

          <div class="text-weight-bold q-mt-sm">
            Parsing finished with warnings
          </div>

          <ul>
            <li
              v-for="(warning, index) in validationWarnings"
              :key="index"
              class="q-mt-sm"
            >
              {{ warning }}
            </li>
          </ul>
        </q-banner>

        <div v-if="validationResult === true && validationData.length" class="q-mt-lg">
          <q-banner class="bg-positive text-white q-mb-md">
            <template #avatar>
              <q-icon name="check_circle"/>
            </template>

            Parsing succeeded.
          </q-banner>

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
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          flat
          label="Close"
          :disable="isValidating"
          v-close-popup
        />

        <q-btn
          unelevated
          color="primary"
          label="Validate"
          icon="check"
          :loading="isValidating"
          :disable="!file"
          @click="validate"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts" generic="T extends ParserPayloadUpdate">
import {computed, ref} from 'vue';
import type {QTableColumn} from "quasar";
import type {ParserPayloadUpdate, ParsingResult} from "src/services/types";

type ParseAction<T> = (
  settings: T,
  file: File,
) => Promise<ParsingResult>;

const isOpen = defineModel<boolean>({
  default: false,
});

const props = defineProps<{
  formData: T;
  parseAction: ParseAction<T>;
  allowedFileType: string
  allowedFileTypeName: string
  parserType: string
}>();

const file = ref<File | null>(null);
const isValidating = ref(false);

const validationData = ref<Record<string, unknown>[]>([]);
const validationError = ref('');
const validationWarnings = ref<string[]>([]);
const validationResult = ref<boolean | null>(null);

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

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value !== 'string') {
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

function isIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value);
}

function resetResult() {
  validationResult.value = null;
}

async function validate() {
  if (!file.value) {
    return;
  }

  isValidating.value = true;
  validationResult.value = null;
  validationData.value = [];
  validationError.value = '';
  validationWarnings.value = [];

  try {
    const result: ParsingResult = await props.parseAction(
      props.formData,
      file.value,
    );

    validationResult.value = result.is_valid;
    validationData.value = result.data;
    validationError.value = result.error;
    validationWarnings.value = result.warnings;
  } finally {
    isValidating.value = false;
  }
}
</script>
