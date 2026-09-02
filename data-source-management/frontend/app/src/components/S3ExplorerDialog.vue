<template>
  <q-dialog
    v-model="showDialog"
    backdrop-filter="blur(4px) saturate(150%)"
    @keydown.esc="showDialog = false"
    @show="onOpen"
  >
    <q-card class="q-pa-sm" style="width: 900px; max-width: 95vw">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">S3 Explorer</div>
        <q-space />
        <div v-if="bucketName" class="text-caption text-grey-7 q-mr-sm">
          Bucket: {{ bucketName }}
        </div>
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>

      <q-card-section class="row items-center q-gutter-sm">
        <q-btn dense flat icon="arrow_upward" :disable="!prefix || loading" @click="goUp">
          <q-tooltip>Up one level</q-tooltip>
        </q-btn>
        <q-breadcrumbs class="text-grey-8" active-color="primary">
          <q-breadcrumbs-el label="/" class="cursor-pointer" @click="navigateTo('')" />
          <q-breadcrumbs-el
            v-for="(segment, index) in breadcrumbs"
            :key="index"
            :label="segment.label"
            class="cursor-pointer"
            @click="navigateTo(segment.prefix)"
          />
        </q-breadcrumbs>
        <q-space />
        <q-btn dense flat icon="create_new_folder" :disable="loading" @click="openNewFolder">
          <q-tooltip>New folder</q-tooltip>
        </q-btn>
        <q-btn dense flat icon="refresh" :disable="loading" @click="refresh">
          <q-tooltip>Refresh</q-tooltip>
        </q-btn>
      </q-card-section>

      <q-card-section class="row items-center q-gutter-sm q-pt-none">
        <q-file
          v-model="fileToUpload"
          dense
          outlined
          class="col"
          label="Choose a file to upload"
          :disable="uploading"
        >
          <template #prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>
        <q-btn
          color="primary"
          icon="upload"
          label="Upload"
          :disable="!fileToUpload"
          :loading="uploading"
          @click="doUpload"
        />
      </q-card-section>

      <q-card-section class="q-pt-none">
        <q-table
          flat
          bordered
          dense
          :rows="rows"
          :columns="columns"
          row-key="key"
          :loading="loading"
          :pagination="{ rowsPerPage: 15 }"
          no-data-label="This folder is empty"
        >
          <template #body-cell-name="props">
            <q-td :props="props">
              <div
                v-if="props.row.is_dir"
                class="row items-center cursor-pointer text-primary"
                @click="openDir(props.row)"
              >
                <q-icon name="folder" class="q-mr-sm" />
                {{ props.row.name }}
              </div>
              <div v-else class="row items-center">
                <q-icon name="insert_drive_file" class="q-mr-sm text-grey-7" />
                {{ props.row.name }}
              </div>
            </q-td>
          </template>

          <template #body-cell-size="props">
            <q-td :props="props">
              {{ props.row.is_dir ? '—' : humanStorageSize(props.row.size) }}
            </q-td>
          </template>

          <template #body-cell-last_modified="props">
            <q-td :props="props">
              {{
                props.row.is_dir || !props.row.last_modified
                  ? '—'
                  : formatDate(props.row.last_modified)
              }}
            </q-td>
          </template>

          <template #body-cell-actions="props">
            <q-td :props="props" class="text-right">
              <q-btn
                v-if="!props.row.is_dir"
                dense
                flat
                round
                icon="download"
                :loading="downloadingKey === props.row.key"
                @click="doDownload(props.row)"
              >
                <q-tooltip>Download</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <q-dialog v-model="newFolderOpen" @keydown.enter="createFolder">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-subtitle1">New folder</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input
            v-model="newFolderName"
            dense
            autofocus
            label="Folder name"
            :rules="[(v) => (!!v && !v.includes('/')) || 'Enter a name without “/”']"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Cancel" color="grey" />
          <q-btn
            flat
            label="Create"
            color="primary"
            :loading="creatingFolder"
            :disable="!newFolderName || newFolderName.includes('/')"
            @click="createFolder"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { QTableColumn } from 'quasar';
import { useQuasar, format, exportFile } from 'quasar';
import type { S3ObjectEntry } from 'src/services/ingest_sftp_storage/types';
import type { IngestStorageService } from 'src/services/factoryIngestStorageService';

const showDialog = defineModel<boolean>({ default: false });
const { ingestId, service, bucketName } = defineProps<{
  ingestId: number;
  service: IngestStorageService;
  bucketName?: string | undefined;
}>();

const $q = useQuasar();

const rows = ref<S3ObjectEntry[]>([]);
const prefix = ref('');
const loading = ref(false);
const uploading = ref(false);
const downloadingKey = ref<string | null>(null);
const fileToUpload = ref<File | null>(null);
const newFolderOpen = ref(false);
const newFolderName = ref('');
const creatingFolder = ref(false);

const columns: QTableColumn<S3ObjectEntry>[] = [
  { name: 'name', label: 'Name', field: 'name', align: 'left', sortable: true },
  { name: 'size', label: 'Size', field: 'size', align: 'right', sortable: true },
  {
    name: 'last_modified',
    label: 'Last Modified',
    field: 'last_modified',
    align: 'left',
    sortable: true,
  },
  { name: 'actions', label: '', field: 'key', align: 'right' },
];

const breadcrumbs = computed(() => {
  const parts = prefix.value.split('/').filter(Boolean);
  let acc = '';
  return parts.map((part) => {
    acc += `${part}/`;
    return { label: part, prefix: acc };
  });
});

async function fetchFiles() {
  loading.value = true;
  try {
    const { data } = await service.listFiles(ingestId, prefix.value);
    rows.value = data;
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to list files' });
  } finally {
    loading.value = false;
  }
}

function onOpen() {
  prefix.value = '';
  fileToUpload.value = null;
  void fetchFiles();
}

function refresh() {
  void fetchFiles();
}

function navigateTo(newPrefix: string) {
  prefix.value = newPrefix;
  void fetchFiles();
}

function openDir(row: S3ObjectEntry) {
  navigateTo(row.key);
}

function goUp() {
  const parts = prefix.value.split('/').filter(Boolean);
  parts.pop();
  navigateTo(parts.length ? `${parts.join('/')}/` : '');
}

async function doUpload() {
  if (!fileToUpload.value) {
    return;
  }
  uploading.value = true;
  try {
    await service.uploadFile(ingestId, fileToUpload.value, prefix.value);
    $q.notify({ type: 'positive', message: 'File uploaded' });
    fileToUpload.value = null;
    await fetchFiles();
  } catch {
    $q.notify({ type: 'negative', message: 'Upload failed' });
  } finally {
    uploading.value = false;
  }
}

function openNewFolder() {
  newFolderName.value = '';
  newFolderOpen.value = true;
}

async function createFolder() {
  const name = newFolderName.value.trim();
  if (!name || name.includes('/')) {
    return;
  }
  creatingFolder.value = true;
  try {
    await service.createDirectory(ingestId, name, prefix.value);
    $q.notify({ type: 'positive', message: 'Folder created' });
    newFolderOpen.value = false;
    await fetchFiles();
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to create folder' });
  } finally {
    creatingFolder.value = false;
  }
}

async function doDownload(row: S3ObjectEntry) {
  downloadingKey.value = row.key;
  try {
    const { data } = await service.downloadFile(ingestId, row.key);
    if (exportFile(row.name, data) !== true) {
      throw new Error('exportFile failed');
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Download failed' });
  } finally {
    downloadingKey.value = null;
  }
}

const { humanStorageSize } = format;

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString();
}
</script>

<style scoped></style>
