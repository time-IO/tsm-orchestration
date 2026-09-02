<template>
  <div v-if="selectedParser" class="q-mb-md">
    <span class="text-caption">Selected Parser: </span>
    <span class="text-caption text-italic text-grey">Name:</span>
    <q-chip dense square color="blue-grey-5" text-color="white">
      {{ selectedParser.name }}
    </q-chip>
    <span class="text-caption text-italic text-grey">Type:</span>
    <q-chip dense square color="lime-5" text-color="white">
      {{ selectedParser.parser_type }}
    </q-chip>

    <template v-if="selectedParser.parser_type === 'csv'">
      <span class="text-caption text-italic text-grey">Delimiter:</span>
      <q-chip dense square color="teal-5" text-color="white">
        {{ selectedParser.delimiter }}
      </q-chip>
      <template v-for="tk in selectedParser.timestamp_columns ?? []" :key="tk.id">
        <span class="text-caption text-italic text-grey">Timestamp Column:</span>
        <q-chip dense square color="light-green-5" text-color="white">
          {{ tk.column }}:{{ tk.timestamp_format }}
        </q-chip>
      </template>
    </template>

    <template v-if="selectedParser.parser_type === 'json'">
      <template v-for="tk in selectedParser.timestamp_keys ?? []" :key="tk.id">
        <span class="text-caption text-italic text-grey">Timestamp Key:</span>
        <q-chip dense square color="light-green-5" text-color="white">
          {{ tk.key }}:{{ tk.format }}
        </q-chip>
      </template>
    </template>

    <template v-if="selectedParser.parser_type === 'soilcan'">
      <span class="text-caption text-italic text-grey">Soilcan-Type:</span>
      <q-chip dense square color="teal-5" text-color="white">
        {{ selectedParser.type }}
      </q-chip>
      <span class="text-caption text-italic text-grey">Header:</span>
      <q-chip dense square color="light-green-5" text-color="white">
        {{ selectedParser.header ? 'Yes' : 'No' }}
      </q-chip>
    </template>

    <q-icon
      name="launch"
      class="cursor-pointer"
      color="blue-grey-5"
      text-color="white"
      @click.stop="openParser(selectedParser.id, selectedParser.parser_type)"
    >
      <q-tooltip>Open in new window</q-tooltip>
    </q-icon>
  </div>

  <q-btn
    outline
    no-caps
    class="q-mb-md full-width"
    icon="tune"
    :label="selectedParser ? 'Update Parser' : 'Select Parser'"
    :disable="disable"
    @click="openDialog"
  >
    <q-tooltip v-if="disable">Select a Permission Group first</q-tooltip>
  </q-btn>

  <q-dialog v-model="showDialog">
    <q-card style="min-width: 400px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Select Parser</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <div class="text-caption q-mb-sm">1. Choose type</div>
        <parser-type-select v-model="dialogParserType" @update:model-value="draftParser = null" />

        <div class="text-caption q-mt-md q-mb-sm" v-if="dialogParserType">2. Choose parser</div>
        <parser-select
          v-if="dialogParserType"
          v-model="draftParser"
          :disable="disable"
          :permission_group_id="permissionGroupId ?? null"
          :parser_type="dialogParserType"
          :preselected_item_id="preselectedParser?.id"
          @update:model-value="onParserPicked"
        />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import ParserTypeSelect from 'components/ParserTypeSelect.vue';
import ParserSelect from 'components/ParserSelect.vue';
import { useRouter } from 'vue-router';
import type { ParserRead, ParserSelectOption } from 'src/services/types';

const selectedParserId = defineModel<number | null | undefined>();
const selectedParser = ref<ParserSelectOption | null>(null);
const draftParser = ref<ParserSelectOption | null>(null);

const props = defineProps<{
  permissionGroupId?: number | null | undefined;
  disable?: boolean | undefined;
  preselectedParser?: ParserRead | null | undefined;
}>();

const showDialog = ref(false);
const dialogParserType = ref<string | null>(props.preselectedParser?.parser_type ?? null);
const router = useRouter();

function openDialog() {
  draftParser.value = selectedParser.value;
  dialogParserType.value =
    selectedParser.value?.parser_type ?? props.preselectedParser?.parser_type ?? null;
  showDialog.value = true;
}

function onParserPicked(parser: ParserSelectOption | null | undefined) {
  if (parser) {
    selectedParser.value = parser;
    selectedParserId.value = parser.id;
    showDialog.value = false;
  }
}

const openParser = (id: number, parser_type: string) => {
  const route = router.resolve({
    path: `/parser/${parser_type}/${id}`,
  });
  window.open(route.href, '_blank');
};

watch(
  () => props.permissionGroupId,
  (newValue, oldValue) => {
    if (oldValue !== null && oldValue !== undefined && oldValue !== newValue) {
      selectedParserId.value = null;
      selectedParser.value = null;
      draftParser.value = null;
      dialogParserType.value = null;
    }
  },
);
watch(
  () => props.preselectedParser,
  (newValue) => {
    if (newValue != null) {
      selectedParser.value = newValue;
      selectedParserId.value = newValue.id;
      dialogParserType.value = newValue.parser_type;
    }
  },
  { immediate: true },
);
</script>

<style scoped></style>
