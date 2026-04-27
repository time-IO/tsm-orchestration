<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Quality Control Setting</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" to="/quality-control" />
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
        <q-tabs v-model="tab" align="left" class="text-grey">
          <q-tab name="basic" label="Basic" />
          <q-tab name="functions" label="Functions" />
        </q-tabs>
        <q-separator />

        <q-tab-panels v-model="tab">
          <q-tab-panel name="basic">
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
                        <q-item-label caption>{{
                          item.permission_group?.name || 'N/A'
                        }}</q-item-label>
                      </q-item-section>
                    </q-item>

                    <q-item>
                      <q-item-section>
                        <q-item-label>Trigger Quality Control Setting</q-item-label>
                        <div>
                          <q-btn
                            class="q-mt-sm"
                            rounded
                            size="sm"
                            label="Go!"
                            @click="openTriggerDialog"
                            text-color="primary"
                          />
                        </div>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </div>
              </div>
            </q-card-section>
          </q-tab-panel>

          <q-tab-panel name="functions">
            <q-card-section>
              <qc-function-arg-list-view
                :quality_control_functions="item.quality_control_functions"
              />
            </q-card-section>
          </q-tab-panel>
        </q-tab-panels>
        <q-card-actions>
          <q-btn :to="editRoute" color="primary" flat> Edit </q-btn>
          <q-space />
          <q-btn :to="copyRoute" color="black" flat> Copy </q-btn>
          <q-space />
          <q-btn color="negative" flat @click="openDeleteDialog"> Delete </q-btn>
        </q-card-actions>
      </q-card>
    </div>
  </q-page>

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

  <trigger-quality-control-settings-dialog
    v-model="showTriggerDialog"
    :ids_to_trigger="selectedIds"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useQualityControlSettingStore } from 'stores/qualityControlSettingStore';
import { useRoute, useRouter } from 'vue-router';
import type { QualityControlSettingPublic } from 'src/services/quality_control_setting/types';
import QcFunctionArgListView from 'components/QcFunctionArgListView.vue';
import TriggerQualityControlSettingsDialog from 'components/TriggerQualityControlSettingsDialog.vue';

const $q = useQuasar();
const store = useQualityControlSettingStore();
const route = useRoute();
const router = useRouter();

const item = ref<QualityControlSettingPublic | null>(null);
const deleteDialog = ref(false);
const isLoading = ref(false);
const tab = ref('basic');

const showTriggerDialog = ref(false);

const id = Number(route.params.id);
const selectedIds = isNaN(id) ? [] : [id];

const basePath = '/quality-control/';

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
      message: 'Failed to load quality control setting data',
    });
  } finally {
    isLoading.value = false;
  }
});

const openDeleteDialog = () => {
  deleteDialog.value = true;
};

const openTriggerDialog = () => {
  showTriggerDialog.value = true;
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
    await router.push(basePath);
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete item',
    });
  } finally {
    deleteDialog.value = false;
  }
};
</script>

<style scoped></style>
