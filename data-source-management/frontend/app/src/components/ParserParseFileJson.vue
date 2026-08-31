<template>
  <parser-parse-file
    allowed-file-type=".json,text/json`"
    allowed-file-type-name="JSON"
    parser-type="JSON"
    :form-data="props.formData"
    :parse-action="jsonParserStore.dispatchParseFile"
  />
</template>

<script setup lang="ts">
import type {JsonParserUpdate} from "src/services/parser_json/types";
import {useJsonParserStore} from "stores/parserJsonStore";
import ParserParseFile from "components/ParserParseFile.vue";

const props = defineProps<{
  formData: JsonParserUpdate;
}>();

const jsonParserStore = useJsonParserStore();
</script>
