<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Parsers</h5>
    <div class="row q-mb-lg">
      <q-space/>
      <q-btn color="green" label="Add Parser" to="/parser/new"/>
    </div>
    <q-table
      :rows="rows"
      :columns="columns"
      row-key="name"
    >
      <template v-slot:body-cell-action="props">
        <q-td :props="props">
          <div>
            <q-btn
              :to="`ingest/${props.row.id}`"
              flat outline color="primary" icon="visibility">
              <q-tooltip>View details</q-tooltip>
            </q-btn>
            <q-btn
              :to="`ingest/${props.row.id}/edit`"
              flat outline color="secondary" icon="edit">
              <q-tooltip>Edit thing</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">

const columns = [
  {
    name: 'id',
    required: true,
    label: 'ID',
    align: 'left',
    field: row => row.id,
    format: val => `${val}`,
    sortable: true
  },
  { name: 'project',label: 'Project', field: 'project', sortable: true , align: 'center'},
  { name: 'name', label: 'Name', field: 'name', sortable: true , align: 'center'},
  {name: 'action', label: 'Actions', align: 'center'}
]

const rows = [
  {
    id: 1,
    project: 'Project 1',
    name: 'Parser 1',
  },
  {
    id: 2,
    project: 'Project 1',
    name: 'Parser 2',
  },
  {
    id: 3,
    project: 'Project 1',
    name: 'Parser 3',
  },
  {
    id: 4,
    project: 'Project 1',
    name: 'Parser 4',
  },
  {
    id: 5,
    project: 'Project 1',
    name: 'Parser 5',
  },
  {
    id: 6,
    project: 'Project 1',
    name: 'Parser 6',
  },
  {
    id: 7,
    project: 'Project 1',
    name: 'Parser 7',
  },
  {
    id: 8,
    project: 'Project 1',
    name: 'Parser 8',
  },
  {
    id: 9,
    project: 'Project 1',
    name: 'Parser 9',
  },
  {
    id: 10,
    project: 'Project 1',
    name: 'Parser 10',
  }
]

</script>

<style scoped>

</style>
