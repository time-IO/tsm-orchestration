<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit JSON Parser</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="detailRoute" />
      </div>
    </div>

    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="save" class="q-gutter-md">
          <!-- Name Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this parser"
            :rules="[(val) => !!val || 'Name is required']"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this parser"
          />

          <parser-timezone-select
            v-model="formData.timezone"
            :rules="[(val: string | null) => !!val || 'Timezone is required']"
          />

          <!-- Timestamp Columns -->
          <div class="q-my-md">
            <div class="row q-gutter-sm items-center q-mb-sm">
              <q-btn
                icon="add"
                label="Add timestamp keys"
                flat
                color="primary"
                @click="addTimestampKeys"
              />
            </div>

            <q-list
              separator
              v-for="(ts, idx) in formData.timestamp_keys"
              :key="idx"
              class="q-mb-sm"
            >
              <q-item>
                <q-item-section>
                  <q-item-label>Timestamp Key {{ idx + 1 }}</q-item-label>
                  <div class="row q-gutter-sm q-mt-xs">
                    <q-input
                      filled
                      class="col"
                      v-model="ts.key"
                      label="Key (e.g. Datetime)"
                      :rules="[
                        (val) => (val !== null && val !== undefined) || 'Column index is required',
                      ]"
                    />
                    <q-input
                      filled
                      class="col"
                      v-model="ts.format"
                      label="Timestamp format (e.g. %Y-%m-%d %H:%M:%S)"
                      :rules="[(val) => !!val || 'Timestamp format is required']"
                    />
                  </div>
                </q-item-section>
                <q-item-section side>
                  <div class="flex items-center">
                    <q-btn
                      dense
                      flat
                      icon="remove_circle"
                      color="red"
                      @click="removeTimestampKeys(idx)"
                    />
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <!-- Validation message for timestamp columns -->
            <div
              v-if="formData.timestamp_keys && formData.timestamp_keys.length === 0"
              class="text-negative q-mt-xs"
            >
              At least one timestamp column is required
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="row q-mt-lg">
            <q-space />
            <div class="col-6">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                :disable="!!formData.timestamp_keys && formData.timestamp_keys.length === 0"
                label="Save"
                class="full-width"
              />
            </div>
            <q-space />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { JsonParserUpdate } from 'src/services/parser_json/types';
import { useJsonParserStore } from 'stores/parserJsonStore';
import ParserTimezoneSelect from 'components/ParserTimezoneSelect.vue';

const permissionGroupStore = usePermissionGroupStore();
const jsonParserStore = useJsonParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<JsonParserUpdate>({
  name: '',
  description: null,
  timestamp_keys: [],
  comment: null,
  timezone: null,
});

const isLoading = ref(false);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await jsonParserStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || '',
        description: data.description || null,
        timestamp_keys: data.timestamp_keys || [],
        comment: data.comment || null,
        timezone: data.timezone,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load parser data',
      });
      await router.push('/parser');
    }
  }

  try {
    await permissionGroupStore.dispatchGetList();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch permission groups',
    });
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/parser/json/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: JsonParserUpdate = {
      name: formData.value.name || '',
      description: formData.value.description || null,
      timestamp_keys: formData.value.timestamp_keys || [],
      comment: formData.value.comment || null,
      timezone: formData.value.timezone || null,
    };

    isLoading.value = true;
    await jsonParserStore.dispatchUpdate(id, data);

    await router.push(detailRoute.value);
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
      timeout: 0,
      actions: [
        {
          icon: 'close',
          color: 'white',
          round: true,
          handler: () => {},
        },
      ],
      message: 'Failed to update parser',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}

function addTimestampKeys() {
  if (formData.value.timestamp_keys) {
    formData.value.timestamp_keys.push({
      key: null,
      format: null,
    });
  }
}

function removeTimestampKeys(index: number) {
  if (formData.value.timestamp_keys) {
    formData.value.timestamp_keys.splice(index, 1);
  }
}
</script>

<style scoped></style>
