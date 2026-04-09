<template>
  <q-list bordered @keyup.enter="triggerEvent">
    <q-expansion-item label="Filter" default-opened>
      <q-card bordered class="q-pa-md">
        <div class="row">
          <div class="col-5">
            <q-input class="q-mb-md" label="Filter by Name" v-model="name" clearable />
          </div>
        </div>
        <div class="row">
          <div class="col-5">
            <permission-group-select
              class="q-mb-md"
              v-model="permission_group_id"
              label="Permission Group"
            />
          </div>
        </div>
        <div class="row">
          <div class="col-5 q-mr-sm">
            <date-time-picker
              clearable
              class="q-mb-md"
              label="Created at from"
              v-model="date_from"
            />
          </div>
          <div class="col-5">
            <date-time-picker clearable class="q-mb-md" label="Created at to" v-model="date_to" />
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

const name = defineModel<string | undefined>('name', { default: undefined });
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
