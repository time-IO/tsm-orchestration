<template>
  <q-select
    v-model="model"
    :options="options"
    filled
    :label="label ? label : 'Select the file encoding *'"
    v-bind="$attrs"
    option-value="codec"
    option-label="codec"
    map-options
    emit-value
    use-input
    @filter="filterFn"
    popup-content-class="limited-dropdown"
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
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';

const store = useParserEncodingStore();
const $q = useQuasar();

const model = defineModel();

defineProps<{
  label?: string;
}>();

const options = ref(store.rows);

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

function filterFn(val: string, update: (cb: () => void) => void) {
  if (val === '') {
    update(() => {
      options.value = store.rows;

      // here you have access to "ref" which
      // is the Vue reference of the QSelect
    });
    return;
  }

  update(() => {
    const needle = val.toLowerCase();

    options.value = store.rows.filter((item) => {
      // Check codec
      if (item.codec.toLowerCase().includes(needle)) return true;

      // Check aliases
      if (item.aliases.some((alias) => alias.toLowerCase().includes(needle))) return true;

      // Check languages
      if (item.languages.some((lang) => lang.toLowerCase().includes(needle))) return true;

      return false;
    });
  });
}
</script>

<style scoped></style>
