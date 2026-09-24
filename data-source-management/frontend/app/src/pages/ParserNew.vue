<template>
  <q-page class="q-pa-lg">
    <h5>Create a new parser</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/parser" />
      </div>
    </div>

    <div class="row q-col-gutter-sm">
      <div class="col-12 col-sm-6 col-md-4 col-lg-3 q-px-xs" v-for="item in data" :key="item.name">
        <q-card class="my-card">
          <q-item style="min-height: 96px; align-items: center">
            <q-item-section avatar>
              <q-avatar :icon="item.icon" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption> {{ item.description }} </q-item-label>
            </q-item-section>
          </q-item>
          <q-separator />
          <q-card-actions>
            <q-space />
            <q-btn :to="item.path" class="full-width" color="green">Create</q-btn>
          </q-card-actions>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
const data = [
  {
    name: 'csv',
    icon: 'folder_copy',
    label: 'CSV',
    description: 'A parser for tabular text data using the python pandas library',
    path: '/parser/new/csv',
  },
  {
    name: 'json',
    icon: 'folder_copy',
    label: 'JSON',
    description: 'An experimental parser for flat JSON data using the python pandas library',
    path: '/parser/new/json',
  },
  {
    name: 'soilcan',
    icon: 'folder_copy',
    label: 'SOILCAN',
    description: 'A parser for ingests associated with SoilCan',
    path: '/parser/new/soilcan',
  },
];
</script>

<style scoped>
.my-card {
  width: 100%;
  max-width: 250px;
}
</style>
