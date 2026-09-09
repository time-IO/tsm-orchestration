<template>
  <q-dialog
    v-model="showDialog"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    no-backdrop-dismiss
  >
    <q-card class="column" style="width: 90vw; height: 80vh">
      <q-card-section class="row items-center">
        <q-space />
        <div class="text-h6">Choose a Quality Control Function</div>
        <q-space />
        <q-btn v-close-popup dense flat icon="close" round />
      </q-card-section>

      <q-separator />

      <q-scroll-area class="col">
        <q-list separator>
          <q-item
            v-for="(item, i) in functionOptions"
            :key="`function-option-${i}`"
            clickable
            v-ripple
            @click="emitSelectFunction(item)"
            @keydown.enter="emitSelectFunction(item)"
            tabindex="0"
          >
            <q-item-section>
              <q-item-label class="text-weight-medium">
                {{ item.label }}
              </q-item-label>
              <q-item-label caption>
                {{ item.description }}
              </q-item-label>
            </q-item-section>

            <q-item-section side>
              <saqc-info-icon :label="item.label" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import type { FunctionOption } from 'src/utils/quality_control_utils';
import SaqcInfoIcon from 'components/SaqcInfoIcon.vue';

const showDialog = defineModel<boolean | null>({ default: false });

const emit = defineEmits(['select']);

const functionOptions: FunctionOption[] = [
  { label: 'flagPlateau', description: 'Flag anomalous value plateaus in a time series.' },
  { label: 'flagIsolated', description: 'Find and flag temporally isolated data groups.' },
  {
    label: 'flagJumps',
    description: 'Flag jumps and drops in data where the mean significantly changes.',
  },
  {
    label: 'flagOffset',
    description: 'Detect and flag spikes or offset value courses in data.',
  },
  {
    label: 'flagRange',
    description: 'Flag values exceeding the given min-max interval.',
  },
  {
    label: 'flagAll',
    description: 'Set the given flag at all unflagged positions.',
  },
  {
    label: 'flagUniLOF',
    description: 'Flag outliers using univariate Local Outlier Factor (LOF).',
  },
  {
    label: 'flagZScore',
    description: 'Flag data points where (rolling) Z-score exceeds threshold.',
  },
  {
    label: 'flagByScatterLowpass',
    description: 'Flag data chunks exceeding a deviation threshold.',
  },
  {
    label: 'flagGeneric',
    description: 'Flag values based on custom conditions',
  },
  {
    label: 'processGeneric',
    description: 'Process data using custom functions.',
  },
  {
    label: 'propagateFlags',
    description: 'Extend existing flags to preceding or subsequent values.',
  },
  {
    label: 'renameField',
    description: 'Rename field to the given name.',
  },
  {
    label: 'rolling',
    description: 'Calculate a rolling-window function on the data.',
  },
  {
    label: 'transferFlags',
    description: 'Transfer flags from one variable to another.',
  },
];

function emitSelectFunction(item: FunctionOption) {
  emit('select', item);
}
</script>

<style scoped></style>
