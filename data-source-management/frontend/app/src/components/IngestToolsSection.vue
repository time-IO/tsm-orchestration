<template>
  <q-card flat bordered class="q-mt-md">
    <q-card-section class="text-subtitle1 text-weight-medium">Ingest Tools</q-card-section>

    <q-separator />

    <q-card-section class="row q-col-gutter-md items-stretch">
      <div v-if="visualizationUrl" :class="service || triggerType ? 'col-12 col-md-6' : 'col-12'">
        <q-card flat bordered class="full-height cursor-pointer column" @click="openGrafana">
          <q-card-section class="col row items-center no-wrap q-pa-md">
            <q-avatar rounded size="2.5rem" color="grey-9">
              <img :src="grafanaLogo" alt="Grafana" />
            </q-avatar>
            <div class="q-ml-md">
              <div class="text-subtitle2 text-weight-medium row items-center no-wrap">
                Grafana Dashboard
                <q-icon name="open_in_new" size="1em" class="q-ml-xs text-grey-6" />
              </div>
              <div class="text-caption text-grey-7">
                Open this ingest's Grafana dashboard to view its incoming data and Journal
                (user-facing logs).
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div v-if="service" class="col-12 col-md-6">
        <q-card
          flat
          bordered
          class="full-height cursor-pointer column"
          @click="explorerOpen = true"
        >
          <q-card-section class="col row items-center no-wrap q-pa-md">
            <q-avatar rounded size="2.5rem" color="primary" text-color="white" icon="folder_open" />
            <div class="q-ml-md">
              <div class="text-subtitle2 text-weight-medium">File Explorer</div>
              <div class="text-caption text-grey-7">
                Browse this ingest's storage bucket: list, upload, and download files, and create
                folders. Changes are written straight to the bucket the ingest delivers into.
              </div>
            </div>
          </q-card-section>
        </q-card>

        <s3-explorer-dialog
          v-model="explorerOpen"
          :ingest-id="ingestId"
          :service="service"
          :bucket-name="bucketName"
        />
      </div>

      <div v-if="triggerType" class="col-12 col-md-6">
        <q-card
          flat
          bordered
          class="full-height cursor-pointer column"
          @click="triggerOpen = true"
        >
          <q-card-section class="col row items-center no-wrap q-pa-md">
            <q-avatar rounded size="2.5rem" color="primary" text-color="white" icon="sync" />
            <div class="q-ml-md">
              <div class="text-subtitle2 text-weight-medium">Trigger Sync</div>
              <div class="text-caption text-grey-7">{{ triggerDescription }}</div>
            </div>
          </q-card-section>
        </q-card>

        <trigger-external-api-dialog
          v-if="triggerType === 'external-api'"
          v-model="triggerOpen"
          :ids_to_trigger="[ingestId]"
        />
        <trigger-external-sftp-dialog
          v-else
          v-model="triggerOpen"
          :ingest_id="ingestId"
        />
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { IngestStorageService } from 'src/services/factoryIngestStorageService';
import { publicAsset } from 'src/utils/public_asset';
import S3ExplorerDialog from 'components/S3ExplorerDialog.vue';
import TriggerExternalApiDialog from 'components/TriggerExternalApiDialog.vue';
import TriggerExternalSftpDialog from 'components/TriggerExternalSftpDialog.vue';

const { uuid, triggerType } = defineProps<{
  uuid?: string | null;
  ingestId: number;
  service?: IngestStorageService | undefined;
  bucketName?: string | undefined;
  triggerType?: 'external-api' | 'external-sftp';
}>();

const explorerOpen = ref(false);
const triggerOpen = ref(false);

const triggerDescription = computed(() =>
  triggerType === 'external-sftp'
    ? "Manually (re)synchronise files from the external SFTP storage into this ingest's internal S3 bucket for a chosen time range."
    : "Manually (re)synchronise this ingest's historic data for a chosen time range.",
);
const grafanaLogo = publicAsset('icons/grafana_icon.png');

const visualizationUrl = computed(() =>
  uuid ? `${window.location.origin}/visualization/d/${encodeURIComponent(uuid)}?orgId=1` : '',
);

function openGrafana() {
  if (visualizationUrl.value) {
    window.open(visualizationUrl.value, '_blank', 'noopener,noreferrer');
  }
}
</script>
