<template>
  <parser-validate-drawer
    allowed-file-type=".csv,text/csv`"
    allowed-file-type-name="CSV"
    parser-type="CSV"
    :parsing-settings="parsingSettings"
    :parse-action="csvParserStore.dispatchValidateFile"
  />
</template>

<script setup lang="ts">
import type { CsvParserValidate } from '@/services/parser_csv/types';
import { useCsvParserStore } from '@/stores/parserCsvStore';
import ParserValidateDrawer from '@/components/ParserValidateDrawer.vue';
import type { ComputedRef } from 'vue';
import { computed, toRaw } from 'vue';
import { formToApi, type CsvParserFormData } from '@/utils/parser_csv_utils';

const props = defineProps<{
  formData: CsvParserFormData;
}>();

const parsingSettings: ComputedRef<CsvParserValidate> = computed(() => {
  const apiData = formToApi(props.formData);

  return {
    delimiter: toRaw(apiData.delimiter ?? null),
    headlines_to_exclude: toRaw(apiData.headlines_to_exclude ?? null),
    footlines_to_exclude: toRaw(apiData.footlines_to_exclude ?? null),
    pandas_read_csv: toRaw(apiData.pandas_read_csv ?? null),
    timestamp_columns: toRaw(apiData.timestamp_columns ?? []),
    comment: toRaw(apiData.comment ?? []),
    header: toRaw(apiData.header ?? null),
    timezone: toRaw(apiData.timezone ?? null),
    encoding: toRaw(apiData.encoding ?? null),
  };
});

const csvParserStore = useCsvParserStore();
</script>
