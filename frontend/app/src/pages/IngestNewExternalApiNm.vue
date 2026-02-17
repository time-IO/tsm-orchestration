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
      <div>{{ timeResolution }}</div>
      <q-input outlined class="q-mb-md" v-model="name" label="Name"/>
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Permission Group *"/>
      <q-input outlined class="q-mb-md" v-model="description" label="Description"/>
      <q-separator class="q-my-lg"/>
      <q-select outlined class="q-mb-md"
                v-model="stationId"
                use-input
                emit-value
                map-options
                clearable
                :options="filteredNeutronMonitorStationOptions"
                @filter="filterNeutronMonitorStation"
                option-value="id"
                option-label="station_id"
                label="Select the station *"
      >
        <template v-slot:option="scope">
          <q-item v-bind="scope.itemProps" clickable>
            <q-item-section>
              <q-item-label>{{ scope.opt.station_id }}</q-item-label>
              <q-item-label caption>{{ scope.opt.description }}</q-item-label>
            </q-item-section>
          </q-item>
        </template>
        <template v-slot:no-option>
          <q-item>
            <q-item-section class="text-grey">
              No results
            </q-item-section>
          </q-item>
        </template>
      </q-select>
      <q-select outlined class="q-mb-md" v-model="timeResolution"
                :options=timeResolutionOptions
                label="Time Resolution"/>

      <div class="row">
        <div class="col col-1">
          <q-checkbox v-model="enableFileServerSync" label="Enable File Server Sync"/>
        </div>
        <div class="col col-2 q-mr-sm">
          <q-input :disable="!enableFileServerSync" outlined class="q-mb-md" v-model="syncInterval"
                   label="Sync interval"/>
        </div>
        <div class="col col-2">
          <q-select :disable="!enableFileServerSync" outlined class="q-mb-md" v-model="unit" :options="unitOptions"
                    label="Unit"/>
        </div>
      </div>
      <q-btn class="full-width " label="Submit" color="green"/>
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useNeutronMonitorStationStore} from "stores/neutronMonitorStationStore";
import {useQuasar} from "quasar";

const neutronMonitorStationStore = useNeutronMonitorStationStore()
const $q = useQuasar()

const filteredNeutronMonitorStationOptions = ref([...neutronMonitorStationStore.neutronMonitorStations])

onMounted(async () => {
  try {
    await neutronMonitorStationStore.dispatchGetList()
  } catch {
    $q.notify({
      position: "top",
      type: 'negative',
      message: 'Failed to fetch neutron monitor stations'
    })
  }
})

const name = ref('')
const project = ref(null)
const stationId = ref(null) // important: this is the id of the station, not the station_id
const timeResolution = ref(null)
const description = ref('')
const projectOptions = [
  'Project 1', 'Project 2', 'Project 3'
]
const enableFileServerSync = ref(false)
const unit = ref(null)
const syncInterval = ref(null)
const unitOptions = [
  'seconds', 'minutes', 'hours', 'days'
]

// value is in minutes
// todo: remove that, just let the use input the minutes
const timeResolutionOptions = [
  {value: "", label: "---------"},
  {value: "0", label: "0 min"},
  {value: "2", label: "2 min"},
  {value: "5", label: "5 min"},
  {value: "10", label: "10 min"},
  {value: "30", label: "30 min"},
  {value: "60", label: "1 h"},
  {value: "120", label: "2 h"},
  {value: "360", label: "6 h"},
  {value: "720", label: "12 h"},
  {value: "1440", label: "1 d"},
  {value: "39276", label: "1 mo"},
  {value: "525969", label: "1 y"}
]

function filterNeutronMonitorStation(val: string, update: (callback: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredNeutronMonitorStationOptions.value = [...neutronMonitorStationStore.neutronMonitorStations]
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    filteredNeutronMonitorStationOptions.value = neutronMonitorStationStore.neutronMonitorStations.filter(v =>
      v.station_id.toLowerCase().includes(needle)
    )
  })
}

</script>

<style scoped>

</style>
