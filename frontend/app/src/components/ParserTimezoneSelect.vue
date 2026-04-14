<template>
  <q-select
    v-model="model"
    :options="options"
    filled
    v-bind="$attrs"
    label="Select the timezone"
    use-input
    @filter="filterFn"
  />
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { onMounted, ref } from 'vue';
import { useParserTimezoneStore } from 'stores/parserTimezoneStore';

const store = useParserTimezoneStore();
const $q = useQuasar();

const model = defineModel();

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
    options.value = store.rows.filter((v) => v.toLowerCase().indexOf(needle) > -1);
  });
}
</script>

<style scoped></style>
