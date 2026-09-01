<template>
  <parser-parse-drawer
    allowed-file-type=".json,text/json`"
    allowed-file-type-name="JSON"
    parser-type="JSON"
    :parsing-settings="parsingSettings"
    :parse-action="jsonParserStore.dispatchParseFile"
  />
</template>

<script setup lang="ts">
import type {JsonParserParse, JsonParserUpdate} from "src/services/parser_json/types";
import {useJsonParserStore} from "stores/parserJsonStore";
import ParserParseDrawer from "components/ParserParseDrawer.vue";
import type {ComputedRef} from "vue";
import { toRaw} from "vue";
import {computed} from "vue";

const props = defineProps<{
  formData: JsonParserUpdate;
}>();

const parsingSettings: ComputedRef<JsonParserParse> = computed(() => {
  return {
    timestamp_keys: toRaw(props.formData.timestamp_keys) ?? [],
    comment: toRaw(props.formData.comment) ?? null,
    timezone: toRaw(props.formData.timezone) ?? null
  }
});

const jsonParserStore = useJsonParserStore();
</script>
