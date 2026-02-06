<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">Neutron Monitor</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <p>
      For more information on Neutronmonitor API properties, visit the API documentation
      <a href="https://www.nmdb.eu/nest/help.php#howto" target="_blank">here</a>.
    </p>
    <q-form>
      <div>{{timeResolution}}</div>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Project" />
      <q-input outlined class="q-mb-md" v-model="description" label="Description" />
      <q-separator class="q-my-lg"/>
      <q-input  outlined class="q-mb-md" v-model="stationId" label="Station Id" />
      <q-select  outlined class="q-mb-md" v-model="timeResolution"
                 :options=timeResolutionOptions
                 label="Time Resolution" />

      <div class="row">
        <div class="col col-1">
          <q-checkbox v-model="enableFileServerSync" label="Enable File Server Sync" />
        </div>
        <div class="col col-2 q-mr-sm">
          <q-input  :disable="!enableFileServerSync" outlined class="q-mb-md" v-model="syncInterval" label="Sync interval" />
        </div>
        <div class="col col-2">
          <q-select :disable="!enableFileServerSync"  outlined class="q-mb-md" v-model="unit" :options="unitOptions" label="Unit" />
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
const timeResolution= ref(null)
const description = ref('')
const projectOptions = [
  'Project 1','Project 2','Project 3'
]
const enableFileServerSync = ref(false)
const unit = ref(null)
const syncInterval = ref(null)
const unitOptions = [
  'seconds', 'minutes','hours', 'days'
]

// value is in minutes
const timeResolutionOptions = [
  {value:"",label:"---------"},
  {value:"0",label:"0 min"},
  {value:"2",label:"2 min"},
  {value:"5",label:"5 min"},
  {value:"10",label:"10 min"},
  {value:"30",label:"30 min"},
  {value:"60",label:"1 h"},
  {value:"120",label:"2 h"},
  {value:"360",label:"6 h"},
  {value:"720",label:"12 h"},
  {value:"1440",label:"1 d"},
  {value:"39276",label:"1 mo"},
  {value:"525969",label:"1 y"}
]

</script>

<style scoped>

</style>
