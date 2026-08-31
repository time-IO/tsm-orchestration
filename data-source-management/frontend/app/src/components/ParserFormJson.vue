<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>

    <div class="text-caption text-grey">Please note: This feature is experimental!</div>

    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="$emit('save')" class="q-gutter-md">
          <!-- Name Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this parser"
            :rules="[rules.REQUIRED]"
          />

          <permission-group-select
            v-model="permissionGroupModel"
            :disable="disablePermissionGroup"
            :rules="[rules.REQUIRED]"
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

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.comment"
            label="Comment character (e.g. //)"
            hint="Character(s) used to indicate comment lines"
          />

          <parser-timezone-select v-model="formData.timezone" :rules="[rules.REQUIRED]" />

          <!-- Timestamp Keys -->
          <div class="q-my-md">
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
                      :rules="[rules.REQUIRED]"
                    />
                    <q-input
                      filled
                      class="col"
                      v-model="ts.format"
                      label="Format (e.g. %Y-%m-%dT%H:%M:%S)"
                      :rules="[rules.REQUIRED, rules.TIMESTAMP_FORMAT]"
                    >
                      <template v-slot:append>
                        <q-btn round flat icon="help_outline" @click="showDocs">
                          <q-tooltip>
                            View Pandas Docs for information on available formatting strings
                          </q-tooltip>
                        </q-btn>
                      </template>
                    </q-input>
                  </div>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    dense
                    flat
                    icon="remove_circle"
                    color="red"
                    @click="removeTimestampKey(idx)"
                  />
                </q-item-section>
              </q-item>
            </q-list>

            <div v-if="formData.timestamp_keys.length === 0" class="text-negative q-mt-xs">
              At least one timestamp key is required
            </div>

            <div class="row q-gutter-sm items-center q-mb-sm">
              <q-btn
                icon="add"
                label="Add timestamp key"
                flat
                color="primary"
                @click="addTimestampKey"
              />
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="row q-mt-lg">
            <q-space/>
            <div class="col-3">
              <q-btn
                unelevated
                color="primary"
                icon="fact_check"
                label="Test parser with file"
                class="full-width"
                @click="showValidationDialog = true"
              />
            </div>
            <q-space />
            <div class="col-6">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                :disable="formData.timestamp_keys.length === 0"
                label="Save"
                class="full-width"
              />
            </div>
            <q-space />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
    <parser-parse-file-json
      v-model="showValidationDialog"
      :form-data="formData"
    />
  </q-page>
</template>

<script setup lang="ts">
import {computed, ref} from 'vue';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import type { JsonParserCreate, JsonParserUpdate } from 'src/services/parser_json/types.ts';
import ParserTimezoneSelect from 'components/ParserTimezoneSelect.vue';
import { rules } from 'src/utils/validation/rules';
import ParserParseFileJson from "components/ParserParseFileJson.vue";

type JsonParserFormData = JsonParserUpdate & {
  permission_group_id?: number | null;
  timestamp_keys: JsonParserCreate['timestamp_keys'];
};

const props = withDefaults(
  defineProps<{
    title: string;
    isLoading: boolean;
    backRoute: string;
    disablePermissionGroup?: boolean;
    permissionGroupId?: number | null;
  }>(),
  {
    disablePermissionGroup: false,
    permissionGroupId: null,
  },
);

defineEmits<{
  save: [];
}>();

const formData = defineModel<JsonParserFormData>({
  default: {
    name: null,
    permission_group_id: null,
    description: null,
    timestamp_keys: [],
    comment: null,
  },
});

const showValidationDialog = ref(false);

const permissionGroupModel = computed({
  get() {
    return formData.value.permission_group_id ?? props.permissionGroupId;
  },
  set(value: number | null) {
    if (!props.disablePermissionGroup) {
      formData.value.permission_group_id = value;
    }
  },
});

function addTimestampKey() {
  formData.value.timestamp_keys.push({
    key: null,
    format: null,
  });
}

function removeTimestampKey(index: number) {
  formData.value.timestamp_keys.splice(index, 1);
}

const showDocs = () => {
  window.open('https://pandas.pydata.org/docs/reference/api/pandas.Period.strftime.html', '_blank');
};
</script>
<style scoped></style>
