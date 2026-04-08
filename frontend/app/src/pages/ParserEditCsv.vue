<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit CSV Parser</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/parser/new" />
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
            hint="Enter a descriptive name for this ingest"
            :rules="[(val) => !!val || 'Name is required']"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this ingest configuration"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.delimiter"
            label="Column delimiter *"
            :rules="[(val) => !!val || 'Column delimiter is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.headlines_to_exclude"
            label="Number of headlines to exclude (0-based)"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.footlines_to_exclude"
            label="Number of footlines to exclude (0-based)"
          />

          <!-- Header Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.header"
            label="Header row index"
            hint="Row index where header is located (0 for first row)"
          />

          <!-- Timestamp Columns -->
          <div class="q-my-md">
            <div class="row q-gutter-sm items-center q-mb-sm">
              <q-btn
                icon="add"
                label="Add timestamp column"
                flat
                color="primary"
                @click="addTimestampColumn"
              />
            </div>

            <q-list
              separator
              v-for="(col, idx) in formData.timestamp_columns"
              :key="idx"
              class="q-mb-sm"
            >
              <q-item>
                <q-item-section>
                  <q-item-label>Timestamp Column {{ idx + 1 }}</q-item-label>
                  <div class="row q-gutter-sm q-mt-xs">
                    <q-input
                      filled
                      type="number"
                      class="col"
                      v-model.number="col.column"
                      label="Column index (0-based)"
                      :rules="[
                        (val) => (val !== null && val !== undefined) || 'Column index is required',
                      ]"
                    />
                    <q-input
                      filled
                      class="col"
                      v-model="col.timestamp_format"
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
                      @click="removeTimestampColumn(idx)"
                    />
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <!-- Validation message for timestamp columns -->
            <div
              v-if="formData.timestamp_columns && formData.timestamp_columns.length === 0"
              class="text-negative q-mt-xs"
            >
              At least one timestamp column is required
            </div>
          </div>

          <!-- Comment Characters -->
          <div class="q-my-md">
            <div v-if="formData.comment">
              <q-list separator v-for="(char, idx) in formData.comment" :key="idx" class="q-mb-sm">
                <q-item>
                  <q-item-section>
                    <q-item-label>Comment Character {{ idx + 1 }}</q-item-label>
                    <q-input
                      filled
                      v-model="formData.comment[idx]"
                      label="Comment character (e.g. #)"
                      type="text"
                      class="col-8"
                    />
                  </q-item-section>
                  <q-item-section side>
                    <q-btn
                      dense
                      flat
                      icon="remove_circle"
                      color="red"
                      @click="removeCommentCharacter(idx)"
                    />
                  </q-item-section>
                </q-item>
              </q-list>
            </div>

            <div class="row q-gutter-sm items-center q-mb-sm">
              <q-btn
                icon="add"
                label="Add comment character"
                flat
                color="primary"
                @click="addCommentCharacter"
              />
            </div>
          </div>

          <q-input
            filled
            v-model="formData.pandas_read_csv"
            label="Pandas read csv"
            type="textarea"
            rows="3"
            hint="additional JSON to configure pandas"
          />

          <!-- Action Buttons -->
          <div class="row q-mt-lg">
            <q-space />
            <div class="col-6">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                :disable="formData.timestamp_columns && formData.timestamp_columns.length === 0"
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
import { onMounted, ref } from 'vue';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { CsvParserUpdate } from 'src/services/parser_csv/types';
import { useCsvParserStore } from 'stores/parserCsvStore';

const permissionGroupStore = usePermissionGroupStore();
const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<CsvParserUpdate>({
  name: null,
  description: null,
  delimiter: null,
  headlines_to_exclude: 0,
  footlines_to_exclude: 0,
  pandas_read_csv: null,
  timestamp_columns: [],
  header: null,
  comment: [],
});

const isLoading = ref(false);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await csvParserStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || null,
        description: data.description || null,
        delimiter: data.delimiter || null,
        headlines_to_exclude: data.headlines_to_exclude || 0,
        footlines_to_exclude: data.footlines_to_exclude || 0,
        pandas_read_csv: data.pandas_read_csv || null,
        timestamp_columns: data.timestamp_columns || [],
        header: data.header ?? null,
        comment: data.comment || [],
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

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: CsvParserUpdate = {
      name: formData.value.name || null,
      description: formData.value.description || null,
      delimiter: formData.value.delimiter || null,
      headlines_to_exclude:
        formData.value.headlines_to_exclude !== null &&
        formData.value.headlines_to_exclude !== undefined
          ? formData.value.headlines_to_exclude
          : null,
      footlines_to_exclude:
        formData.value.footlines_to_exclude !== null &&
        formData.value.footlines_to_exclude !== undefined
          ? formData.value.footlines_to_exclude
          : null,
      pandas_read_csv: formData.value.pandas_read_csv || null,
      timestamp_columns: formData.value.timestamp_columns || [],
      header:
        formData.value.header !== null && formData.value.header !== undefined
          ? formData.value.header
          : null,
      comment: formData.value.comment || [],
    };

    isLoading.value = true;
    await csvParserStore.dispatchUpdate(id, data);

    await router.push(`/parser/csv/${id}`);
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
      progress: true,
      message: 'Failed to update parser',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}

function addTimestampColumn() {
  if (formData.value.timestamp_columns) {
    formData.value.timestamp_columns.push({
      column: null,
      timestamp_format: null,
    });
  }
}

function removeTimestampColumn(index: number) {
  if (formData.value.timestamp_columns) {
    formData.value.timestamp_columns.splice(index, 1);
  }
}

function addCommentCharacter() {
  if (formData.value.comment) {
    formData.value.comment.push('');
  }
}

function removeCommentCharacter(index: number) {
  if (formData.value.comment) {
    formData.value.comment.splice(index, 1);
  }
}
</script>

<style scoped></style>
