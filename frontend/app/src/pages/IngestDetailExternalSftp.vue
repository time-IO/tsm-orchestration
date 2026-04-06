<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">External SFTP Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" :to="backUrl" />
      </div>
    </div>

    <div v-if="isLoading" class="q-pa-md">
      <q-spinner color="primary" size="3em" />
    </div>

    <div v-else-if="item">
      <q-card>
        <q-card-section>
          <div class="text-h4">{{ item.name }}</div>
          <div class="text-subtitle1">{{ item.description }}</div>
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="row q-col-gutter-md">
            <div class="col-md-6">
              <q-list>
                <q-item>
                  <q-item-section>
                    <q-item-label>ID</q-item-label>
                    <q-item-label caption>{{ item.id }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>UUID</q-item-label>
                    <q-item-label caption>{{ item.uuid }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Permission Group</q-item-label>
                    <q-item-label caption>{{ item.permission_group?.name || 'N/A' }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Filename Pattern</q-item-label>
                    <q-item-label caption>{{ item.filename_pattern }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Fileserver URI</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ item.uri }}</q-item-label>
                      <q-btn
                        flat
                        round
                        icon="content_copy"
                        size="sm"
                        @click="copyClipboard(item.uri)"
                        title="Copy fileserver uri"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Username</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ item.username }}</q-item-label>
                      <q-btn
                        flat
                        round
                        icon="content_copy"
                        size="sm"
                        @click="copyClipboard(item.username)"
                        title="Copy username"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Password</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption class="col-2">
                        <q-input
                          borderless
                          v-model="item.password"
                          :type="isPwd ? 'password' : 'text'"
                        >
                          <template v-slot:prepend>
                            <q-icon
                              :name="isPwd ? 'visibility_off' : 'visibility'"
                              class="cursor-pointer"
                              @click="isPwd = !isPwd"
                            />
                          </template>
                        </q-input>
                      </q-item-label>
                      <q-btn
                        flat
                        round
                        icon="content_copy"
                        size="sm"
                        @click="copyClipboard(item.password)"
                        title="Copy password"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Public Key</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ shortenText(item.ssh_public_key) }}</q-item-label>
                      <q-btn
                        flat
                        round
                        icon="content_copy"
                        size="sm"
                        @click="copyClipboard(item.ssh_public_key)"
                        title="Copy public key"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Created At (UTC)</q-item-label>
                    <q-item-label caption>{{ formatDate(item.created_at) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>

            <div class="col-md-6">
              <q-list>
                <q-item>
                  <q-item-section>
                    <q-item-label>Parser</q-item-label>
                    <q-item-label caption>
                      {{ item.csv_parser.name }}
                      <q-icon name="launch" class="cursor-pointer" @click="openParser">
                        <q-tooltip> Open in new window </q-tooltip>
                      </q-icon>
                    </q-item-label>
                  </q-item-section>
                </q-item>
                <q-item>
                  <q-item-section>
                    <q-item-label>Sync Enabled</q-item-label>
                    <q-item-label caption>
                      <q-badge :color="item.sync_enabled ? 'positive' : 'negative'">
                        {{ item.sync_enabled ? 'Yes' : 'No' }}
                      </q-badge>
                    </q-item-label>
                  </q-item-section>
                </q-item>

                <q-item v-if="item.sync_enabled">
                  <q-item-section>
                    <q-item-label>Sync Interval</q-item-label>
                    <q-item-label caption>
                      {{ item.sync_interval_in_minutes }} minutes
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions>
          <q-btn :to="editRoute" color="primary" flat> Edit </q-btn>
          <q-space />
          <q-btn color="negative" flat @click="openDeleteDialog"> Delete </q-btn>
        </q-card-actions>
      </q-card>
    </div>

    <q-dialog v-model="deleteDialog" persistent>
      <q-card>
        <q-card-section>
          <h6 class="q-mt-none">Confirm Delete</h6>
        </q-card-section>

        <q-card-section> Are you sure you want to delete this item? </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup color="primary" flat label="Cancel" />
          <q-space />
          <q-btn color="negative" flat label="Delete" @click="deleteItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { copyToClipboard, useQuasar } from 'quasar';
import type { IngestExternalSftpPublic } from 'src/services/ingest_external_sftp/types';
import { useIngestExternalSftpStore } from 'stores/ingestExternalSftpStore';

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const store = useIngestExternalSftpStore();

const item = ref<IngestExternalSftpPublic | null>(null);
const deleteDialog = ref(false);
const isLoading = ref(false);
const isPwd = ref(true);

const backUrl = '/ingest/external-sftp';

onMounted(async () => {
  try {
    isLoading.value = true;
    const id = Number(route.params.id);

    if (!isNaN(id)) {
      item.value = await store.dispatchGetOne(id);
    }
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to load ingest data',
    });
  } finally {
    isLoading.value = false;
  }
});

const editRoute = computed(() => {
  if (item.value?.id) {
    return `/ingest/external-sftp/${item.value.id}/edit`;
  }
  return '';
});

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

const openDeleteDialog = () => {
  deleteDialog.value = true;
};

const deleteItem = async () => {
  if (!item.value) {
    return;
  }

  try {
    await store.dispatchDelete(item.value.id);
    $q.notify({
      type: 'positive',
      message: 'Item deleted successfully',
    });
    await router.push(backUrl);
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete item',
    });
  } finally {
    deleteDialog.value = false;
  }
};

const openParser = () => {
  if (item.value && item.value.csv_parser) {
    const route = router.resolve({
      path: `/parser/csv/${item.value.csv_parser.id}`,
    });

    window.open(route.href, '_blank');
  }
};

const copyClipboard = (text: string | null) => {
  if (!text) {
    return;
  }

  copyToClipboard(text)
    .then(() => {
      $q.notify({
        message: 'Copied to clipboard',
        color: 'positive',
        icon: 'check',
      });
    })
    .catch(() => {
      $q.notify({
        message: 'Failed to copy',
        color: 'negative',
        icon: 'error',
      });
    });
};

const shortenText = (key: string) => {
  if (!key) return '';
  // Show first 10 chars, last 10 chars, and middle dots
  if (key.length <= 25) return key;
  return `${key.substring(0, 10)}...${key.substring(key.length - 10)}`;
};
</script>

<style scoped></style>
