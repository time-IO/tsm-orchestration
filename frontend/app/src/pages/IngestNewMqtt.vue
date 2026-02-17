<template>
  <q-page class="q-pa-lg">
    <h5>New MQTT Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <q-form>
      <q-input outlined class="q-mb-md" v-model="name" label="Name"/>
      <q-select outlined class="q-mb-md" v-model="project" :options="projectOptions" label="Permission Group *"/>
      <q-input outlined class="q-mb-md" v-model="description" label="Description"/>
      <q-separator class="q-my-lg"/>
      <q-list bordered class="q-mb-md">
        <q-expansion-item
          label="Stuff that will be generated"
        >
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="Username"/>
          <q-input outlined disable class="q-mb-md q-mx-md" model-value="" label="Password"/>
        </q-expansion-item>
      </q-list>
      <q-input outlined class="q-mb-md" v-model="brokerUri" label="Broker URI"/>
      <q-input outlined class="q-mb-md" v-model="topic" label="Topic"/>
      <q-select outlined class="q-mb-md"
                v-model="mqttParserId"
                use-input
                emit-value
                map-options
                clearable
                :options="filteredMqttParserOptions"
                @filter="filterMqttParser"
                option-value="id"
                option-label="name"
                label="Select the parser *"
      >
        <template v-slot:no-option>
          <q-item>
            <q-item-section class="text-grey">
              No results
            </q-item-section>
          </q-item>
        </template>
      </q-select>

      <q-btn class="full-width " label="Submit" color="green"/>

    </q-form>


  </q-page>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useQuasar} from "quasar";
import {useMqttParserStore} from "stores/mqttParserStore";

const name = ref('')
const brokerUri = ref('')
const topic = ref('')
const description = ref('')
const project = ref(null)
const mqttParserId = ref(null)
const projectOptions = [
  'Project 1', 'Project 2', 'Project 3'
]

const $q = useQuasar()
const mqttParserStore = useMqttParserStore()

const filteredMqttParserOptions = ref([...mqttParserStore.mqttParsers])

onMounted(async () => {
  try {
    await mqttParserStore.dispatchGetList()
  } catch {
    $q.notify({
      position: "top",
      type: 'negative',
      message: 'Failed to fetch parser options'
    })
  }
})

function filterMqttParser(val: string, update: (callback: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredMqttParserOptions.value = [...mqttParserStore.mqttParsers]
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    filteredMqttParserOptions.value = mqttParserStore.mqttParsers.filter(v =>
      v.name.toLowerCase().includes(needle)
    )
  })
}

</script>

<style scoped>

</style>
