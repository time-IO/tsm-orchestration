<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">SFTP Ingest</h5>
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
          <div class="text-h5 ellipsis" style="max-width: 100%">{{ item.name }}</div>
          <q-tooltip>
            {{ item.name }}
          </q-tooltip>
          <div class="text-subtitle1" style="max-width: 100%">{{ item.description }}</div>
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
                    <div class="row items-center">
                      <q-item-label caption>{{ item.uuid }}</q-item-label>
                      <copy-btn title="Copy UUID" :text-to-copy="item.uuid" />
                    </div>
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
                      <q-item-label caption>{{ item.fileserver_uri }}</q-item-label>
                      <copy-btn title="Copy fileserver URI" :text-to-copy="item.fileserver_uri" />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Bucket Name</q-item-label>
                    <q-item-label caption>{{ item.bucket_name }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Username</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ item.username }}</q-item-label>
                      <copy-btn title="Copy username" :text-to-copy="item.username" />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Password</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>
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
                      <copy-btn title="Copy username" :text-to-copy="item.password" />
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
                      {{ item.parser.name }}
                      <q-icon name="launch" class="cursor-pointer" @click="openParser">
                        <q-tooltip> Open in new window </q-tooltip>
                      </q-icon>
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
          <q-btn :to="copyRoute" color="black" flat> Copy </q-btn>
          <q-space />
          <!--          <q-btn color="negative" flat @click="openDeleteDialog"> Delete </q-btn>-->
        </q-card-actions>
      </q-card>

      <ingest-tools-section
        :uuid="item.uuid"
        :ingest-id="item.id"
        :service="API.ingestSftpStorage"
        :bucket-name="item.bucket_name"
      />
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
import { useQuasar } from 'quasar';
import type { IngestSftpPublic } from 'src/services/ingest_sftp/types';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import CopyBtn from 'components/CopyBtn.vue';
import IngestToolsSection from 'components/IngestToolsSection.vue';
import { API } from 'src/services';

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const store = useIngestSftpStore();

const item = ref<IngestSftpPublic | null>(null);
const deleteDialog = ref(false);
const isLoading = ref(false);
const isPwd = ref(true);

const backUrl = '/ingest';

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

const basePath = '/ingest/sftp/';

const editRoute = computed(() => {
  if (item.value?.id) {
    return `${basePath}${item.value.id}/edit`;
  }
  return '';
});
const copyRoute = computed(() => {
  if (item.value?.id) {
    return `${basePath}${item.value.id}/copy`;
  }
  return '';
});

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

// const openDeleteDialog = () => {
//   deleteDialog.value = true;
// };

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
  if (item.value?.parser?.id && item.value?.parser?.parser_type) {
    const route = router.resolve({
      path: `/parser/${item.value.parser.parser_type}/${item.value.parser.id}`,
    });

    window.open(route.href, '_blank');
  }
};
</script>

<style scoped></style>
