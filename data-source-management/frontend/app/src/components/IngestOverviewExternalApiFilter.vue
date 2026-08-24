<template>
  <q-list bordered @keyup.enter="triggerEvent">
    <q-expansion-item label="Filter" default-opened>
      <q-card bordered class="q-pa-md">
        <div class="row q-gutter-x-sm">
          <div class="col-3">
            <q-input class="q-mb-sm" label="Filter by Name" v-model="name" clearable dense />
          </div>
          <span></span>
          <div class="col-3">
            <q-input
              class="q-mb-sm"
              label="Filter by UUID"
              v-model="uuid"
              clearable
              dense
              @blur="trimUuid"
            />
          </div>
        </div>
        <div class="row q-gutter-x-sm">
          <div class="col-3 q-mr-sm">
            <permission-group-select
              class="q-mb-sm"
              v-model="permission_group_id"
              label="Permission Group"
              dense
            />
          </div>
          <div class="col-3">
            <ingest-external-api-type-select class="q-mb-sm" v-model="api_type" dense />
          </div>
        </div>
        <div class="row q-gutter-x-sm">
          <div class="col-3 q-mr-sm">
            <date-time-picker
              clearable
              class="q-mb-sm"
              label="Created at from"
              v-model="date_from"
              dense
            />
          </div>
          <div class="col-3">
            <date-time-picker
              clearable
              class="q-mb-sm"
              label="Created at to"
              v-model="date_to"
              dense
            />
          </div>
        </div>
        <q-card-actions class="column items-end q-gutter-sm" style="margin-top: -48px">
          <q-btn @click="resetFilters" style="min-width: 120px">Clear filter</q-btn>
          <q-btn @click="triggerEvent" style="min-width: 120px">Apply filter</q-btn>
        </q-card-actions>
      </q-card>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import DateTimePicker from 'components/DateTimePicker.vue';
import IngestExternalApiTypeSelect from 'components/IngestExternalApiTypeSelect.vue';

const name = defineModel<string | undefined>('name', { default: undefined });
const uuid = defineModel<string | undefined>('uuid', { default: undefined });
const api_type = defineModel<string | undefined>('api_type', { default: undefined });
const permission_group_id = defineModel<number | undefined>('permission_group_id', {
  default: undefined,
});
const date_from = defineModel<string | undefined>('date_from', { default: undefined });
const date_to = defineModel<string | undefined>('date_to', { default: undefined });

const emit = defineEmits(['applyFilters']);

function triggerEvent() {
  emit('applyFilters');
}

function resetFilters() {
  name.value = undefined;
  uuid.value = undefined;
  api_type.value = undefined;
  permission_group_id.value = undefined;
  date_from.value = undefined;
  date_to.value = undefined;
  emit('applyFilters');
}
function trimUuid() {
  if (uuid.value) {
    uuid.value = uuid.value.trim();
  }
}
</script>

<style scoped></style>
