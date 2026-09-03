<template>
  <div class="result-table-wrap" :class="{ 'validation-table--stale': isStale }">
    <q-table
      flat
      bordered
      dense
      :rows="data"
      :columns="tableColumns"
      row-key="__row"
      :pagination="{ rowsPerPage: 10 }"
      :rows-per-page-options="[10, 25, 50]"
      wrap-cells
      separator="cell"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { QTableColumn } from 'quasar';
import { unknownToString } from 'src/utils/string_utils';

const props = defineProps<{
  data: Record<string, unknown>[];
  isStale: boolean;
}>();

const tableColumns = computed<QTableColumn[]>(() => {
  const firstRow = props.data[0];
  if (!firstRow) {
    return [];
  }
  return Object.keys(firstRow).map((key) => ({
    name: key,
    label: key,
    field: key,
    align: 'left',
    format: (value: unknown) => unknownToString(value),
  }));
});
</script>

<style scoped>
.result-table-wrap {
  overflow: hidden;
  min-height: 0;
  flex: 0 1 auto;
}

.result-table-wrap :deep(.q-table__container) {
  max-height: 100%;
}

.validation-table--stale {
  opacity: 0.4;
}
</style>
