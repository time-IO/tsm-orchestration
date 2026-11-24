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
      <q-card-section style="white-space: pre-line">{{ resolved.textHelp }}</q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const HELP_TERMS: Record<string, { titleHelp: string; textHelp: string }> = {
  sync_interval: {
    titleHelp: 'Sync Interval',
    textHelp:
      'Number of minutes between automatic synchronization runs.\n\n' +
      'Syncs are scheduled with a cron expression, which can only repeat evenly within ' +
      'an hour or a day. The interval is therefore rounded down to the nearest value ' +
      'a cron expression can resolve:\n' +
      '• up to 60 minutes: every 10, 12, 15, 20, 30 or 60 minutes\n' +
      '• up to a day: every 1, 2, 3, 4, 6, 8, 12 or 24 hours\n' +
      '• more than a day: whole days\n\n' +
      'Example: 45 minutes runs every 30 minutes, 300 minutes (5 hours) runs every 4 hours.',
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
