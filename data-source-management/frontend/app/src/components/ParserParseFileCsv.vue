<template>
  <parser-parse-file
    allowed-file-type=".csv,text/csv`"
    allowed-file-type-name="CSV"
    parser-type="CSV"
    :form-data="props.formData"
    :parse-action="csvParserStore.dispatchParseFile"
  />
</template>

<script setup lang="ts">
import type {CsvParserUpdate} from "src/services/parser_csv/types";
import {useCsvParserStore} from "stores/parserCsvStore";
import ParserParseFile from "components/ParserParseFile.vue";

const props = defineProps<{
  formData: CsvParserUpdate;
}>();

const csvParserStore = useCsvParserStore();
</script>
