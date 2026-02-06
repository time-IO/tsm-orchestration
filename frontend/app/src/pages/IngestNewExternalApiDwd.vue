<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">Deutscher Wetterdienst</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <p>
      For more information on Deutscher Wetterdienst API properties, visit the API documentation
      <a href="https://brightsky.dev/docs/#/operations/getWeather" target="_blank">here</a>.
    </p>
    <q-form>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Permission Group *" />
      <q-input outlined class="q-mb-md" v-model="description" label="Description" />
      <q-separator class="q-my-lg"/>
      <q-input  outlined class="q-mb-md" v-model="stationId" label="Station Id" hint="ID of the DWD weather station (usually 5 numeric characters)"/>
      <div class="row">
        <div class="col col-1">
          <q-checkbox v-model="enableFileServerSync" label="Enable File Server Sync" />
        </div>
        <div class="col col-2 q-mr-sm">
          <q-input  disable outlined class="q-mb-md" v-model="syncInterval" label="Sync interval" />
        </div>
        <div class="col col-2">
          <q-select disable  outlined class="q-mb-md" v-model="unit" :options="unitOptions" label="Unit" />
        </div>
      </div>
      <q-btn class="full-width " label="Submit" color="green"/>
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const name = ref('')
const project= ref(null)
const stationId= ref(null)
const description = ref('')
const projectOptions = [
  'Project 1','Project 2','Project 3'
]
const enableFileServerSync = ref(false)
const unit = ref('minutes')
const syncInterval = ref(1440)

const unitOptions = [
  'seconds', 'minutes','hours', 'days'
]
</script>

<style scoped>

</style>
