<template>
  <div class="result-table-wrap column no-wrap">
    <q-table
      flat
      bordered
      dense
      :rows="rows"
      :columns="tableColumns"
      row-key="__row"
      :pagination="{ rowsPerPage: 10 }"
      :rows-per-page-options="[10, 25, 50]"
      wrap-cells
      separator="cell"
    >
      <template v-if="hasDates && !timezonesAreEqual" #top>
        <div class="row no-wrap items-center q-gutter-x-md">
          <q-select
            v-model="displayTimezone"
            :options="timezoneOptions"
            label="Display timezone"
            emit-value
            map-options
            borderless
            dense
          >
            <template #selected>
              <span class="ellipsis" :title="selectedTimezoneOption?.label">
                {{ selectedTimezoneOption?.label }}
              </span>
            </template>
          </q-select>
        </div>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { QTableColumn } from 'quasar';
import { unknownToString } from '@/utils/string_utils';
import { formatDate, parseIsoTimestamp } from '@/utils/time_utils';

const props = defineProps<{
  data: Record<string, unknown>[];
  parserTimezone: string | null;
}>();

type DisplayTimezone = 'parser' | 'browser';

const displayTimezone = ref<DisplayTimezone>('parser');

const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

// ISO timestamps are converted to Dates once, so they can be rendered in any timezone
const rows = computed(() =>
  props.data.map((row) =>
    Object.fromEntries(
      Object.entries(row).map(([key, value]) => [key, parseIsoTimestamp(value) ?? value]),
    ),
  ),
);

const hasDates = computed(() =>
  rows.value.some((row) => Object.values(row).some((value) => value instanceof Date)),
);

const timezonesAreEqual = computed(() => props.parserTimezone === browserTimezone);

const timeZones = computed<Record<DisplayTimezone, string>>(() => ({
  parser: props.parserTimezone ?? 'UTC',
  browser: browserTimezone,
}));

const timezoneOptions = computed(() => [
  { value: 'parser', label: `Parser timezone (${timeZones.value.parser})` },
  { value: 'browser', label: `Local timezone (${browserTimezone})` },
]);

const selectedTimezoneOption = computed(() =>
  timezoneOptions.value.find((option) => option.value === displayTimezone.value),
);

const tableColumns = computed<QTableColumn[]>(() => {
  const firstRow = props.data[0];
  if (!firstRow) {
    return [];
  }
  const timeZone = timeZones.value[displayTimezone.value];
  return Object.keys(firstRow).map((key) => ({
    name: key,
    label: key,
    field: key,
    align: 'left',
    format: (value: unknown) =>
      value instanceof Date ? formatDate(value, timeZone) : unknownToString(value),
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
  flex: 0 1 auto;
  min-height: 0;
}
</style>
