<template>
  <q-card flat bordered class="q-mt-md">
    <q-card-section class="text-subtitle1 text-weight-medium">SMS Configurations</q-card-section>

    <q-separator />

    <q-card-section>
      <div class="text-caption text-grey-7 q-mb-md">
        <span v-if="configurations.length"
          >SMS configurations this ingest is linked to. Open one to view its devices, mounts and
          metadata in the Sensor Management System.</span
        >
        <span v-else>
          The Sensor Management System allows you to manage sensors, measurement setups and
          campaigns. Once you link data from time.IO with metadata from SMS, linked Configurations
          will appear here.
        </span>
      </div>

      <q-list v-if="configurations.length" bordered separator class="rounded-borders">
        <q-item v-for="(config, index) in configurations" :key="config.url ?? index">
          <q-item-section>
            <q-item-label class="text-subtitle2 text-weight-medium overflow-auto">
              {{ truncateText(config.label, 50) }}
            </q-item-label>
          </q-item-section>

          <q-item-section v-if="config.url" side>
            <q-btn
              flat
              round
              dense
              icon="open_in_new"
              color="grey-7"
              @click="openInNewTab(config.url)"
            >
              <q-tooltip>Open in new tab</q-tooltip>
            </q-btn>
          </q-item-section>
        </q-item>
      </q-list>

      <div v-else class="text-caption">
        <p>To link a configuration with this ingest, do the following:</p>

        <ol class="link-steps q-mt-sm">
          <li class="row no-wrap items-start q-mb-sm">
            <div class="step-number bg-grey-6 text-white">1</div>
            <div class="col">
              Go to the
              <span class="text-weight-bold">Sensor Management System (SMS)</span>
              <q-btn
                flat
                dense
                round
                size="xs"
                icon="open_in_new"
                color="grey-7"
                class="q-ml-xs"
                type="a"
                :href="smsUrl"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open the Sensor Management System in a new tab"
              >
                <q-tooltip>Open SMS in a new tab</q-tooltip>
              </q-btn>
              and create a Configuration or open an existing one.
            </div>
          </li>

          <li class="row no-wrap items-start q-mb-sm">
            <div class="step-number bg-grey-6 text-white">2</div>
            <div class="col">
              Go to the tab <span class="text-weight-bold">Data Linking</span> and fill the form
              accordingly.
            </div>
          </li>

          <li class="row no-wrap items-start q-mb-sm">
            <div class="step-number bg-grey-6 text-white">3</div>
            <div class="col">
              Select
              <span class="text-weight-bold">{{ databaseName }}</span>
              as Datasource and <span class="text-weight-bold">ingestName</span> as Thing.
            </div>
          </li>
        </ol>

        <p>
          Learn more about the detailed connection process on our

          <span class="text-weight-bold">Wiki page</span>
          <q-btn
            flat
            dense
            round
            size="xs"
            icon="open_in_new"
            color="grey-7"
            class="q-ml-xs"
            type="a"
            href="https://codebase.helmholtz.cloud/ufz-tsm/timeio-support/-/wikis/Metadata"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open the Sensor Management System in a new tab"
          >
            <q-tooltip>Open SMS in a new tab</q-tooltip> </q-btn
          >.
        </p>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { API } from '@/services';
import { truncateText } from '@/utils/string_utils';

const { ingestId } = defineProps<{
  ingestId: number;
}>();

export type SmsConfiguration = {
  label: string;
  url: string;
};

const configurations = ref<SmsConfiguration[]>([]);
const databaseName = ref<string>('');
const smsUrl = ref<string>('https://web.app.ufz.de/sms');

onMounted(async () => {
  if (!ingestId) return;
  configurations.value = await API.smsConfigurations.getConfigurationsByIngest(ingestId);
  databaseName.value = await API.ingestDatabase.getDatabaseName(ingestId);
});

function openInNewTab(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer');
}
</script>
<style scoped>
.link-steps {
  list-style: none;
  margin: 0;
  padding-left: 0;
}

.step-number {
  flex: 0 0 18px;
  width: 18px;
  height: 18px;
  margin-right: 8px;
  border-radius: 50%;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
  font-weight: 500;
}
</style>
