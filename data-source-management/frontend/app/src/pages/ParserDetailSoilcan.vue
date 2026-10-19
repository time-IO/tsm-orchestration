<template>
  <q-page class="q-pa-lg">
    <h5>SOILCAN Parser</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" to="/parser" />
      </div>
    </div>
    <div v-if="isLoading" class="q-pa-md">
      <q-spinner color="primary" size="3em" />
    </div>
    <div v-else-if="item">
      <q-card>
        <q-card-section>
          <div class="row items-start no-wrap">
            <div class="col">
              <div class="text-h5 ellipsis" style="max-width: 100%">{{ item.name }}</div>
              <q-tooltip>
                {{ item.name }}
              </q-tooltip>
              <div class="text-subtitle1" style="max-width: 100%">{{ item.description }}</div>
            </div>

            <q-btn-dropdown
              color="light-blue-8"
              unelevated
              icon="add"
              label="Create Ingest"
              class="q-ml-md"
            >
              <q-list>
                <q-item
                  v-for="ingestType in availableIngestTypes"
                  :key="ingestType.value"
                  clickable
                  v-close-popup
                  :to="createIngestRoute(ingestType.value)"
                >
                  <q-item-section>{{ ingestType.label }}</q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </div>
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
                    <q-item-label>Created at (UTC)</q-item-label>
                    <q-item-label caption>{{ formatDate(item.created_at) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
            <div class="col-md-6">
              <q-list>
                <q-item>
                  <q-item-section>
                    <q-item-label>Type</q-item-label>
                    <q-item-label caption>{{ item.type }}</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item>
                  <q-item-section>
                    <q-item-label>Header</q-item-label>
                    <q-item-label caption>
                      <q-badge :color="item.header ? 'positive' : 'negative'">
                        {{ item.header ? 'Yes' : 'No' }}
                      </q-badge>
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
          <q-btn color="negative" flat @click="openDeleteDialog"> Delete </q-btn>
        </q-card-actions>
      </q-card>
    </div>
    <q-dialog v-model="deleteDialog" persistent>
      <q-card>
        <q-card-section>
          <h6 class="q-mt-none">Confirm deletion</h6>
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

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { useSoilcanParserStore } from '@/stores/parserSoilcanStore';
import { computed, onMounted, ref } from 'vue';
import type { SoilcanParserPublic } from '@/services/parser_soilcan/types';

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const store = useSoilcanParserStore();

const item = ref<SoilcanParserPublic | null>(null);
const deleteDialog = ref(false);
const isLoading = ref(false);

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

const basePath = '/parser/soilcan/';

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

const availableIngestTypes = [
  { value: 'external-sftp', label: 'External SFTP' },
  { value: 'sftp', label: 'SFTP' },
];

function createIngestRoute(ingestTypeValue: string) {
  if (!item.value?.id) return '';
  return {
    path: `/ingest/new/${ingestTypeValue}`,
    query: { parserId: String(item.value.id), parserType: 'soilcan' },
  };
}

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
      position: 'top',
      type: 'positive',
      message: 'Item deleted successfully',
    });
    await router.push('/parser');
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    let errorCaption = error?.response?.data?.detail || '';

    // if it is a validation error, then error.response.data.detail is an array of objects [{type:string, loc: string[], msg: string, input: any, probably an object}]
    if (typeof errorCaption === 'object') {
      errorCaption = errorCaption[0].msg;
    }
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to delete item',
      caption: errorCaption,
    });
  } finally {
    deleteDialog.value = false;
  }
};
</script>

<style scoped></style>
