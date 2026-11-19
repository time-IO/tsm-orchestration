<template>
  <q-dialog :model-value="option !== null" @update:model-value="onDialogToggle">
    <q-card v-if="option" style="width: 640px; max-width: 90vw">
      <q-card-section class="row items-center no-wrap">
        <q-icon name="input" size="sm" class="q-mr-sm" />
        <div class="text-h6">{{ option.label }}</div>
        <q-space />
        <q-btn icon="close" flat round dense aria-label="Close" @click="emit('close')" />
      </q-card-section>

      <q-card-section class="q-pt-none">
        <IngestDataFlow :type="option.flow" :source-label="sourceLabel" />
      </q-card-section>

      <q-card-section class="q-pt-none">
        <p>{{ option.helpText }}</p>
        <div class="text-subtitle1 text-weight-medium">Choose this ingest if</div>
        <q-list dense>
          <q-item v-for="reason in option.chooseIf" :key="reason" class="q-px-none">
            <q-item-section avatar style="min-width: 32px">
              <q-icon name="check" color="primary" />
            </q-item-section>
            <q-item-section>{{ reason }}</q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import IngestDataFlow from '@/components/IngestDataFlow.vue';
import type { IngestOption } from '@/components/ingestOptions';

defineProps<{
  option: IngestOption | null;
  sourceLabel?: string | undefined;
}>();

const emit = defineEmits<{
  close: [];
}>();

function onDialogToggle(open: boolean) {
  if (!open) emit('close');
}
</script>
