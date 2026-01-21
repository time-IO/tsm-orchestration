<template>
  <q-page class="q-pa-lg">
    <h5>New MQTT Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <q-form>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Project" />
      <q-input outlined class="q-mb-md" v-model="description" label="Description" />
      <q-separator class="q-my-lg"/>
      <q-list bordered class="q-mb-md">
        <q-expansion-item
          label="Stuff that will be generated"
        >
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="Username" />
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="Password" />
        </q-expansion-item>
      </q-list>
      <q-input  outlined class="q-mb-md" v-model="brokerUri" label="Broker URI" />
      <q-input  outlined class="q-mb-md" v-model="topic" label="Topic" />
      <q-select outlined class="q-mb-md" v-model="mqttModel" :options="mqttOptions" label="Parser" />

      <q-btn class="full-width " label="Submit" color="green"/>

    </q-form>


  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const name = ref('')
const brokerUri = ref('')
const topic = ref('')
const description = ref('')
const project= ref(null)
const mqttModel= ref(null)
const projectOptions = [
  'Project 1','Project 2','Project 3'
]
const mqttOptions = [
  'MQTT Device 1','MQTT Device 2','MQTT Device 3'
]

</script>

<style scoped>

</style>
