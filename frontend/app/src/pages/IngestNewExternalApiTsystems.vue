<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">TSystems</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <p>
      For more information on TSystems API properties, visit the API documentation
      <a href="https://sensorstation.caritc.de/sensorstation-management/swagger-ui/index.html" target="_blank">here</a>.
    </p>
    <q-form>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Project" />
      <q-input outlined class="q-mb-md" v-model="description" label="Description" />
      <q-separator class="q-my-lg"/>

      <q-input  outlined class="q-mb-md" v-model="stationId" label="Station Id" />
      <q-input  outlined class="q-mb-md" v-model="group" label="Group" />


      <q-input outlined class="q-mb-md" v-model="username" label="Username" />
      <q-input outlined class="q-mb-md" v-model="password" :type="isPwd ? 'password' : 'text'" label="Password">
        <template v-slot:append>
          <q-icon
            :name="isPwd ? 'visibility_off' : 'visibility'"
            class="cursor-pointer"
            @click="isPwd = !isPwd"
          />
        </template>
      </q-input>

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
const description = ref('')
const projectOptions = [
  'Project 1','Project 2','Project 3'
]
const isPwd= ref(true)

const stationId= ref(null)
const group = ref(null)

const enableFileServerSync = ref(false)
const unit = ref('minutes')
const syncInterval = ref(60)

const username = ref('')
const password = ref('')

const unitOptions = [
  'seconds', 'minutes','hours', 'days'
]

</script>

<style scoped>

</style>
