<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute"/>
      </div>
    </div>

    <div class="text-caption text-grey">
      For more information visit the time.IO Wiki
      <a
        href="https://codebase.helmholtz.cloud/ufz-tsm/timeio-support/-/wikis/TimeIO-Frontend#csv-parser"
        target="_blank"
      >here</a
      >.
    </div>

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
            :rules="[rules.REQUIRED, ruleFactories.MAX(80)]"
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
            v-model="formData.delimiter"
            label="Column delimiter * (e.g. , ; \t)"
            :rules="[rules.REQUIRED]"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.headlines_to_exclude"
            @update:model-value="trimHeadlines"
            label="Number of headlines to exclude"
            hint="Enter either a single number to indicate of many lines should be excluded or a comma-separated list of numbers indicating the lines which must be excluded (0-based)"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.footlines_to_exclude"
            label="Number of footlines to exclude"
          />

          <parser-timezone-select v-model="formData.timezone" :rules="[rules.REQUIRED]"/>

          <parser-encoding-select v-model="formData.encoding" :rules="[rules.REQUIRED]"/>

          <!-- Header Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.header"
            label="Header row index"
            hint="Row index where header is located (0 for first row)"
            :rules="[rules.INTEGER, ruleFactories.MIN(0)]"
          />

          <!-- Timestamp Columns -->
          <div class="q-my-md">
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
                      :rules="[rules.REQUIRED]"
                    />
                    <q-input
                      filled
                      class="col"
                      v-model="col.timestamp_format"
                      label="Timestamp format (e.g. %Y-%m-%d %H:%M:%S)"
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
            <div v-if="formData.timestamp_columns.length === 0" class="text-negative q-mt-xs">
              At least one timestamp column is required
            </div>

            <div class="row q-gutter-sm items-center q-mb-sm">
              <q-btn
                icon="add"
                label="Add timestamp column"
                flat
                color="primary"
                @click="addTimestampColumn"
              />
            </div>
          </div>

          <!-- Comment Characters -->
          <div class="q-my-md">
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
            <q-space/>
            <div class="col-3">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                :disable="formData.timestamp_columns.length === 0"
                label="Save"
                class="full-width"
              />
            </div>
            <q-space/>
          </div>
        </q-form>
      </q-card-section>
    </q-card>
    <parser-parse-file-csv
      v-model="showValidationDialog"
      :form-data="formData"
    />
  </q-page>
</template>

<script setup lang="ts">
import {computed, ref} from 'vue';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import type {CsvParserCreate, CsvParserUpdate} from 'src/services/parser_csv/types';
import ParserEncodingSelect from 'components/ParserEncodingSelect.vue';
import ParserTimezoneSelect from 'components/ParserTimezoneSelect.vue';
import {ruleFactories, rules} from 'src/utils/validation/rules';
import ParserParseFileCsv from "components/ParserParseFileCsv.vue";

type CsvParserFormData = CsvParserUpdate & {
  permission_group_id?: number | null;
  timestamp_columns: CsvParserCreate['timestamp_columns'];
  comment: string[];
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

const formData = defineModel<CsvParserFormData>({
  default: {
    permission_group_id: null,
    name: null,
    description: null,
    delimiter: null,
    headlines_to_exclude: 0,
    footlines_to_exclude: 0,
    pandas_read_csv: null,
    timestamp_columns: [],
    comment: [],
    header: null,
    timezone: null,
    encoding: null,
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

function addTimestampColumn() {
  formData.value.timestamp_columns.push({
    column: null,
    timestamp_format: null,
  });
}

function removeTimestampColumn(index: number) {
  formData.value.timestamp_columns.splice(index, 1);
}

function addCommentCharacter() {
  formData.value.comment.push('');
}

function removeCommentCharacter(index: number) {
  formData.value.comment.splice(index, 1);
}

const showDocs = () => {
  window.open('https://pandas.pydata.org/docs/reference/api/pandas.Period.strftime.html', '_blank');
};

function trimHeadlines(value: string | number | null) {
  formData.value.headlines_to_exclude = String(value ?? '').trim();
}
</script>

<style scoped></style>
