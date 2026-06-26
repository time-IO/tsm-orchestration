<template>
  <q-btn round flat icon="help_outline" class="text-grey" @click="dialog = true">
    <q-tooltip>More information</q-tooltip>
  </q-btn>
  <q-dialog v-model="dialog">
    <q-card style="min-width: 400px">
      <q-card-section class="row items-center">
        <div class="text-h6">{{ resolved.titleHelp }}</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      <q-card-section>{{ resolved.textHelp }}</q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const HELP_TERMS: Record<string, { titleHelp: string; textHelp: string }> = {
  sync_interval: {
    titleHelp: 'Sync Interval',
    textHelp: ' Number of minutes between automatic synchronization runs',
  },
  period: {
    titleHelp: 'Period',
    textHelp: 'Number of minutes to look back during each synchronization',
  },
};

const props = defineProps<{
  titleHelp?: string;
  textHelp?: string;
  termHelp?: string;
}>();

const resolved = computed<{ titleHelp: string; textHelp: string }>(() => {
  if (props.termHelp && HELP_TERMS[props.termHelp]) {
    return HELP_TERMS[props.termHelp]!;
  }
  return { titleHelp: props.titleHelp ?? '', textHelp: props.textHelp ?? '' };
});

const dialog = ref(false);
</script>
