<template>
  <div class="result-table-wrap column no-wrap">
    <q-table
      ref="table"
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
    <teleport-into :target="table" selector=".q-table__bottom">
      <!-- append to #bottom slot -->
      <div
        v-if="timestamps.length > 0 && !timezonesAreEqual"
        class="result-table__timezone full-width row no-wrap items-center justify-end"
      >
        <span class="q-table__bottom-item text-no-wrap">Displayed timezone:</span>
        <q-select
          v-model="displayTimezone"
          :options="timezoneOptions"
          emit-value
          map-options
          class="q-table__select q-table__bottom-item"
          borderless
          dense
        >
          <template #selected>
            <span class="ellipsis" :title="selectedOption?.label">
              {{ selectedOption?.label }}
            </span>
          </template>
        </q-select>
      </div>
    </teleport-into>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useTemplateRef } from 'vue';
import type { QTableColumn } from 'quasar';
import TeleportInto from '@/components/common/TeleportInto.vue';
import { unknownToString } from '@/utils/string_utils';
import { formatIsoTimestamp, formatIsoTimestampAsLocal } from '@/utils/time_utils';
import { isIsoDate } from '@/utils/validation/validators';

const props = defineProps<{
  data: Record<string, unknown>[];
  parserTimezone: string | null;
}>();

type DisplayTimezone = 'parser' | 'browser';

const displayTimezone = ref<DisplayTimezone>('parser');
const table = useTemplateRef('table');

const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

const timestamps = computed(() =>
  props.data.flatMap((row) =>
    Object.values(row).filter((v): v is string => typeof v === 'string' && isIsoDate(v)),
  ),
);

const timezonesAreEqual = computed(() => props.parserTimezone === browserTimezone);

// timestamps are returned in the parser's timezone, so only the local view needs a conversion
const formatters = { parser: formatIsoTimestamp, browser: formatIsoTimestampAsLocal };

const timezoneOptions = computed(() => [
  {
    value: 'parser',
    label: props.parserTimezone ? `Parser time (${props.parserTimezone})` : 'Parser time',
  },
  { value: 'browser', label: `Local time (${browserTimezone})` },
]);

const selectedOption = computed(() =>
  timezoneOptions.value.find((option) => option.value === displayTimezone.value),
);

const tableColumns = computed<QTableColumn[]>(() => {
  const firstRow = props.data[0];
  if (!firstRow) {
    return [];
  }
  const format = formatters[displayTimezone.value];
  return Object.keys(firstRow).map((key) => ({
    name: key,
    label: key,
    field: key,
    align: 'left',
    format: (value: unknown) =>
      typeof value === 'string' && isIsoDate(value) ? format(value) : unknownToString(value),
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

/* move teleported content in slot before Quasar's pagination */
.result-table__timezone {
  order: -1;
}
</style>
