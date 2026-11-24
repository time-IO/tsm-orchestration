<template>
  <q-card flat bordered>
    <q-card-section class="q-pb-sm">
      <div class="row items-center no-wrap">
        <div class="col">
          <div v-if="title" class="text-weight-medium">{{ title }}</div>
          <div v-if="subtitle" class="text-caption text-grey-7">{{ subtitle }}</div>
        </div>
        <q-badge :color="entry.enabled ? 'positive' : 'grey-6'" :label="status" />
      </div>

      <div class="row q-col-gutter-md q-mt-none">
        <div class="col-12 col-sm-4">
          <div class="text-caption text-grey-7">Cron expression (UTC)</div>
          <code class="text-body2">{{ entry.cron_expression }}</code>
        </div>
        <div class="col-6 col-sm-4">
          <div class="text-caption text-grey-7">Start delay</div>
          <div>{{ entry.jitter_seconds }} s</div>
        </div>
        <div v-if="interval !== undefined" class="col-6 col-sm-4">
          <div class="text-caption text-grey-7">Sync interval</div>
          <div>{{ interval === null ? 'not set' : `${interval} min` }}</div>
        </div>
      </div>
    </q-card-section>

    <template v-if="entry.next_runs.length">
      <q-separator />
      <q-card-section class="q-py-sm">
        <div class="text-caption text-grey-7 q-mb-xs">Next runs (UTC)</div>
        <q-chip
          v-for="run in entry.next_runs"
          :key="run"
          dense
          outline
          size="sm"
          class="q-ma-none q-mr-xs q-mb-xs"
        >
          {{ formatUtc(run) }}
        </q-chip>
      </q-card-section>
    </template>

    <q-separator />
    <q-card-section class="q-py-xs text-caption text-grey-7">
      Last changed {{ formatUtc(entry.updated_at) }} UTC
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { IngestSchedule, ScheduledJob } from '@/services/ingest_schedule/types';

const { entry } = defineProps<{
  entry: IngestSchedule | ScheduledJob;
  interval?: number | null;
  title?: string;
  subtitle?: string | null;
}>();

const status = computed(() => (entry.enabled ? 'active' : 'paused'));

function formatUtc(iso: string): string {
  return new Date(iso).toISOString().slice(0, 19).replace('T', ' ');
}
</script>
