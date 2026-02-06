<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">The Things network</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <p>
      For more information on The Things Network API properties, visit the API documentation
      <a href="https://www.thethingsindustries.com/docs/api/" target="_blank">here</a>.
    </p>
    <q-form>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Permission Group *" />
      <q-input outlined class="q-mb-md" v-model="description" label="Description" />
      <q-separator class="q-my-lg"/>

      <q-input outlined class="q-mb-md" v-model="endpointUri" label="Endpoint-URI" />
      <q-input outlined class="q-mb-md" v-model="apiKey" :type="isPwd ? 'password' : 'text'" label="Api Key">
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
const description = ref('')
const isPwd= ref(true)
const endpointUri = ref('')
const apiKey = ref('')
const projectOptions = [
  'Project 1','Project 2','Project 3'
]

const enableFileServerSync = ref(false)
const unit = ref('minutes')
const syncInterval = ref(60)

const unitOptions = [
  'seconds', 'minutes','hours', 'days'
]

</script>

<style scoped>

</style>
