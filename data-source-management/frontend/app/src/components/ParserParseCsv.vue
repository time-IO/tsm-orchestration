<template>
  <parser-parse-drawer
    allowed-file-type=".csv,text/csv`"
    allowed-file-type-name="CSV"
    parser-type="CSV"
    :parsing-settings="parsingSettings"
    :parse-action="csvParserStore.dispatchParseFile"
  />
</template>

<script setup lang="ts">
import type { CsvParserParse, CsvParserUpdate } from 'src/services/parser_csv/types';
import { useCsvParserStore } from 'stores/parserCsvStore';
import ParserParseDrawer from 'components/ParserParseDrawer.vue';
import type { ComputedRef } from 'vue';
import { computed, toRaw } from 'vue';

const props = defineProps<{
  formData: CsvParserUpdate;
}>();

const parsingSettings: ComputedRef<CsvParserParse> = computed(() => {
  return {
    delimiter: toRaw(props.formData.delimiter ?? null),
    headlines_to_exclude: toRaw(props.formData.headlines_to_exclude ?? null),
    footlines_to_exclude: toRaw(props.formData.footlines_to_exclude ?? null),
    pandas_read_csv: toRaw(props.formData.pandas_read_csv ?? null),
    timestamp_columns: toRaw(props.formData.timestamp_columns ?? []),
    comment: toRaw(props.formData.comment ?? []),
    header: toRaw(props.formData.header ?? null),
    timezone: toRaw(props.formData.timezone ?? null),
    encoding: toRaw(props.formData.encoding ?? null),
  };
});

const csvParserStore = useCsvParserStore();
</script>
