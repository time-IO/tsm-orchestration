<template>
  <q-select
    v-model="model"
    :options="store.rows"
    filled
    label="Select the file encoding"
    v-bind="$attrs"
    option-value="codec"
    option-label="codec"
    map-options
    emit-value
  >
    <template v-slot:option="scope">
      <q-item v-bind="scope.itemProps" clickable>
        <q-item-section>
          <q-item-label>{{ scope.opt.codec }}</q-item-label>
          <q-item-label caption>aliases: {{ scope.opt.aliases.join(',') }}</q-item-label>
          <q-item-label caption>languages: {{ scope.opt.languages.join(',') }}</q-item-label>
        </q-item-section>
      </q-item>
    </template>
    <template v-slot:no-option>
      <q-item>
        <q-item-section class="text-grey"> No results </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { useParserEncodingStore } from 'stores/parserEncodingStore';
import { onMounted } from 'vue';
import { useQuasar } from 'quasar';

const store = useParserEncodingStore();
const $q = useQuasar();

const model = defineModel();

onMounted(async () => {
  try {
    await store.dispatchGetList();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch stations',
    });
  }
});
</script>

<style scoped></style>
