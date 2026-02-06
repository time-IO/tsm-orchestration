<template>
  <q-page class="q-pa-lg">
    <h5>New SFTP Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <q-form>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Permission Group *" />
      <q-input outlined class="q-mb-md" v-model="description" label="Description" />
      <q-separator class="q-my-lg"/>
      <q-list bordered class="q-mb-md">
        <q-expansion-item
          label="Stuff that will be generated"
        >
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="File Server URI" />
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="Username" />
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="Password" />
        </q-expansion-item>
      </q-list>
      <q-input  outlined class="q-mb-md" disable model-value="CSV" label="Parser Type" />
      <q-input  outlined class="q-mb-md" v-model="fileNamePattern" label="File Name Pattern" />
      <q-select outlined class="q-mb-md" v-model="parserModel" :options="parserOptions" label="Parser" />

      <q-btn class="full-width " label="Submit" color="green"/>

    </q-form>


  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const name = ref('')
const fileNamePattern = ref('')
const description = ref('')
const project= ref(null)
const parserModel= ref(null)
const projectOptions = [
  'Project 1','Project 2','Project 3'
]
const parserOptions = [
  'Parser 1','Parser 2','Parser 3'
]

</script>

<style scoped>

</style>
