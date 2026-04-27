<template>
  <q-dialog
    v-model="showDialog"
    backdrop-filter="blur(4px) saturate(150%)"
    full-height
    full-width
    persistent
  >
    <q-card>
      <q-card-section class="row">
        <q-space />
        <div class="text-h6">Choose a quality control function</div>
        <q-space />
        <q-btn v-close-popup dense flat icon="close" round />
      </q-card-section>
      <q-separator inset />
      <div class="q-pa-md row items-start q-gutter-md">
        <q-card
          v-for="(item, i) in functionOptions"
          @click="emitSelectFunction(item)"
          :key="`function-option-${i}`"
          style="width: 24%"
          class="q-hoverable"
        >
          <span class="q-focus-helper"></span>
          <q-card-section>
            <q-item>
              <q-item-section>
                <span class="text-h6">{{ item.label }}</span>
              </q-item-section>
              <q-item-section side>
                <q-icon
                  name="info"
                  class="cursor-pointer"
                  @click.stop="openSaqcDocuForFunction(item.label)"
                >
                  <q-tooltip> Open SaQC Documentation </q-tooltip>
                </q-icon>
              </q-item-section>
            </q-item>
          </q-card-section>
          <q-separator />
          <q-card-section> {{ item.description }}</q-card-section>
        </q-card>
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import type { FunctionOption } from 'src/utils/quality_control_utils';

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

function openSaqcDocuForFunction(functionName: string) {
  const url = `https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.${functionName}`;
  window.open(url, '_blank');
}
</script>

<style scoped></style>
