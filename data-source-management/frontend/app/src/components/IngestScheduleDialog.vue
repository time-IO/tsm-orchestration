<template>
  <q-dialog
    v-model="showDialog"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @show="load"
  >
    <q-card class="column no-wrap" style="width: 640px; max-width: 90vw; max-height: 80vh">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Sync Schedule</div>
        <q-space />
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>

      <q-card-section class="q-pb-none">
        <q-banner rounded dense class="bg-blue-1 text-blue-10">
          <template #avatar><q-icon name="info" color="blue-8" /></template>
          To spread the load as evenly as possible, every sync gets its own start time: the schedule
          fixes the minute (and hour or day) within the interval, and an additional delay of up to
          59 seconds is added. Both are chosen randomly when the schedule is created and stay
          unchanged when the sync interval is modified. All times are in UTC.
        </q-banner>
      </q-card-section>

      <q-card-section v-if="isLoading" class="row justify-center q-pa-lg">
        <q-spinner color="primary" size="2em" />
      </q-card-section>

      <q-card-section v-else-if="hasError" class="text-negative">
        Could not load the schedule.
      </q-card-section>

      <q-card-section v-else-if="info" class="scroll q-gutter-y-md">
        <div>
          <div class="text-subtitle2 q-mb-sm">Regular sync</div>
          <schedule-entry v-if="info.schedule" :entry="info.schedule" />
          <div v-else class="text-grey-7">
            No schedule configured, external sync is not set up for this ingest.
          </div>
        </div>

        <div v-if="info.jobs.length || isSuperuser">
          <div class="row items-center q-mb-sm">
            <div class="text-subtitle2">Custom jobs</div>
            <q-space />
            <q-btn
              v-if="isSuperuser"
              dense
              flat
              color="primary"
              icon="add"
              label="Add custom job"
              @click="openForm(null)"
            />
          </div>
          <div v-if="!info.jobs.length" class="text-grey-7">No custom jobs defined.</div>
          <schedule-entry
            v-for="job in info.jobs"
            :key="job.id"
            :entry="job"
            :title="jobLabel(job)"
            :subtitle="job.note"
            class="q-mb-sm"
          >
            <template v-if="isSuperuser && job.ingest_id !== null" #actions>
              <q-btn dense flat round size="sm" icon="edit" @click="openForm(job)" />
              <q-btn dense flat round size="sm" icon="delete" color="negative" @click="remove(job)" />
            </template>
          </schedule-entry>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>

  <ingest-custom-job-dialog
    v-if="isSuperuser"
    v-model="formOpen"
    :ingest-id="ingestId"
    :job="editedJob"
    @saved="load"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { API } from '@/services';
import { useAuthStore } from '@/stores/authStore';
import type { IngestScheduleInfo, CustomJob } from '@/services/ingest_schedule/types';
import ScheduleEntry from '@/components/IngestScheduleEntry.vue';
import IngestCustomJobDialog from '@/components/IngestCustomJobDialog.vue';

const { ingestId } = defineProps<{ ingestId: number }>();
const showDialog = defineModel<boolean>({ default: false });

const $q = useQuasar();
const isSuperuser = computed(() => useAuthStore().userInfo?.is_superuser ?? false);

const formOpen = ref(false);
const editedJob = ref<CustomJob | null>(null);

const info = ref<IngestScheduleInfo | null>(null);
const isLoading = ref(false);
const hasError = ref(false);

function openForm(job: CustomJob | null) {
  editedJob.value = job;
  formOpen.value = true;
}

async function deleteJob(job: CustomJob) {
  try {
    await API.ingestSchedule.deleteCustomJob(ingestId, job.id);
    await load();
  } catch {
    $q.notify({ type: 'negative', position: 'top', message: 'Failed to delete the custom job.' });
  }
}

function remove(job: CustomJob) {
  $q.dialog({
    title: 'Delete custom job',
    message: `Delete "${jobLabel(job)}"?`,
    cancel: true,
    persistent: true,
  }).onOk(() => {
    void deleteJob(job);
  });
}

function jobLabel(job: CustomJob): string {
  const days = job.params.days;
  switch (job.job_type) {
    case 'sync_thing':
      return 'Additional sync';
    case 'resync_thing':
      return `Resync of the last ${days} days`;
    case 'resync_project':
      return `Resync of the last ${days} days (all external-API ingests of the project)`;
    case 'sync_sms':
      return `SMS sync (${job.params.origin})`;
    default:
      return job.job_type;
  }
}

async function load() {
  isLoading.value = true;
  hasError.value = false;
  try {
    info.value = await API.ingestSchedule.getSchedule(ingestId);
  } catch {
    hasError.value = true;
  } finally {
    isLoading.value = false;
  }
}
</script>
