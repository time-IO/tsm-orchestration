<template>
  <q-list bordered @keyup.enter="triggerEvent">
    <q-expansion-item label="Filter" default-opened>
      <q-card bordered class="q-pa-md">
        <div class="row">
          <div class="col-3">
            <q-input class="q-mb-sm" label="Filter by Name" v-model="name" clearable dense />
          </div>
        </div>
        <div class="row">
          <div class="col-3 q-mr-sm">
            <permission-group-select
              class="q-mb-sm"
              v-model="permission_group_id"
              label="Permission Group"
              dense
            />
          </div>
          <div class="col-3">
            <parser-type-select class="q-mb-sm" v-model="parser_type" dense />
          </div>
        </div>
        <div class="row">
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

        <q-card-actions>
          <q-space></q-space>
          <q-btn @click="triggerEvent">Apply filter</q-btn>
        </q-card-actions>
      </q-card>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import DateTimePicker from 'components/DateTimePicker.vue';
import ParserTypeSelect from 'components/ParserTypeSelect.vue';

const name = defineModel<string | undefined>('name', { default: undefined });
const parser_type = defineModel<string | undefined>('parser_type', { default: undefined });
const permission_group_id = defineModel<number | undefined>('permission_group_id', {
  default: undefined,
});
const date_from = defineModel<string | undefined>('date_from', { default: undefined });
const date_to = defineModel<string | undefined>('date_to', { default: undefined });

const emit = defineEmits(['applyFilters']);

function triggerEvent() {
  emit('applyFilters');
}
</script>

<style scoped></style>
