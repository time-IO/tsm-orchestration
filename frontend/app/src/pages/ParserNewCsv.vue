<template>
  <q-page class="q-pa-lg">
    <h5>New CSV Parser</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/parser/new" />
      </div>
    </div>
    <q-form>
      <q-input  outlined class="q-mb-md" v-model="name" label="Name" />
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Project" />
      <q-input outlined  class="q-mb-md" v-model="description" label="Description" />
      <q-separator/>
      <q-input  outlined class="q-mb-md" v-model="columnDelimiter" label="Column Delimiter" />
      <q-input  outlined class="q-mb-md" v-model="headerLinesToExclude" label="Headlines to Exclude" />
      <q-input  outlined class="q-mb-md" v-model="footerLinesToExclude" label="Footer Lines to Exclude" />
      <q-input  outlined class="q-mb-md" v-model="commentMarkers" label="Comment markers (separated by spaces)" />

      <p>Timestamp columns</p>
      <q-btn class="q-mb-md" outline  @click="addItemToTimestampColumns">Add Column</q-btn>
      <template v-for="(item,index) in timestampColumns" :key="index">
        <div class="row items-center">
          <div class="col col-2 q-mr-sm">
            <q-input  outlined class="q-mb-md" v-model="item.column" label="Column" />
          </div>
          <div class="col col-2">
            <q-input  outlined class="q-mb-md" v-model="item.format" label="Timestamp format" />
          </div>
          <div class="col col-1">
            <q-btn
              @click="removeItemFromTimestampColumns(index)"
              :disable="timestampColumns.length<2" outline flat class="q-mb-md" color="red" icon="delete"/>
          </div>
        </div>
      </template>

      <q-expansion-item
        class="q-mb-md"
        expand-separator
        label="Extended setting"
      >
        <q-input
          type="textarea"
          outlined class="q-mb-md" v-model="extraSettings" label="Pandas Read CSV" />

      </q-expansion-item>

      <q-btn class="full-width " label="Submit" color="green"/>
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const name = ref('')
const description = ref('')
const project= ref(null)
const columnDelimiter = ref('')

const headerLinesToExclude = ref(0)
const footerLinesToExclude = ref(0)
const commentMarkers = ref('')

const timestampColumns = ref([{column:0,format:''}])

const extraSettings = ref('')

const projectOptions = [
  'Project 1','Project 2','Project 3'
]

const addItemToTimestampColumns = ()=>{
  const columnNumber = timestampColumns.value.length
  timestampColumns.value.push({column:columnNumber,format:''})
}

const removeItemFromTimestampColumns = (index:number) => {
  timestampColumns.value.splice(index,1)
}


</script>

<style scoped></style>
