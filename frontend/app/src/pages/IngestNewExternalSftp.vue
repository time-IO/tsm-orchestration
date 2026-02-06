<template>
  <q-page class="q-pa-lg">
    <h5>New External SFTP Ingest</h5>
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
      <q-input outlined class="q-mb-md" v-model="fileServerUri" label="File Server URI" />
      <q-input outlined class="q-mb-md" v-model="path" label="Path" />
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
const isPwd= ref(true)
const fileNamePattern = ref('')
const fileServerUri = ref('')
const path = ref('')
const username = ref('')
const password = ref('')
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
