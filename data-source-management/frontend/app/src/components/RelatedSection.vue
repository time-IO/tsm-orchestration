<template>
  <q-card flat bordered class="q-mt-md">
    <q-card-section class="text-subtitle1 text-weight-medium">Related</q-card-section>

    <q-separator />

    <q-tabs
      v-model="tab"
      dense
      align="left"
      no-caps
      class="text-grey-7"
      active-color="primary"
      indicator-color="primary"
      narrow-indicator
    >
      <q-tab name="configurations" label="SMS Configurations" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="configurations" class="q-pa-md">
        <related-section-list
          :items="configurations"
          empty-label="No configurations linked to this ingest."
        >
          <template #description>
            SMS configurations this ingest is linked to. Open one to view its devices, mounts and
            metadata in the Sensor Management System.
          </template>
        </related-section-list>
      </q-tab-panel>
    </q-tab-panels>
  </q-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import RelatedSectionList from '@/components/RelatedSectionList.vue';
import { API } from '@/services';

const { ingestId } = defineProps<{
  ingestId: number;
}>();

export type SmsConfiguration = {
  label: string;
  url: string;
};

const configurations = ref<SmsConfiguration[]>([]);

onMounted(async () => {
  if (!ingestId) return;
  configurations.value = await API.smsConfigurations.getConfigurationsByIngest(ingestId);
});

const tab = ref<'configurations' | 'sta'>('configurations');
</script>
