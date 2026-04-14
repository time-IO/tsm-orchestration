<template>
  <q-select
    v-model="model"
    :options="store.rows"
    filled
    v-bind="$attrs"
    label="Select the timezone"
  ></q-select>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { onMounted } from 'vue';
import { useParserTimezoneStore } from 'stores/parserTimezoneStore';

const store = useParserTimezoneStore();
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
