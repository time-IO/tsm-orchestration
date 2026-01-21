<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">Umweltbundesamt (UBA) Air Data</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new"/>
      </div>
    </div>
    <div class="text-caption text-grey">
      For more information on UBA Air Data API properties, visit the
      <a href="https://luftqualitaet.api.bund.dev/" target="_blank" class="text-primary">API documentation</a>.
    </div>


    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="save" class="q-gutter-md">
          <!-- Name Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this ingest"
            :rules="[val => !!val || 'Name is required']"
          />

          <!-- Project Selection -->
          <q-select
            filled
            v-model="formData.project_id"
            :options="projectOptions"
            label="Project *"
            option-value="id"
            option-label="label"
            emit-value
            map-options
            hint="Select the project this ingest belongs to"
            :rules="[val => !!val || 'Project is required']"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this ingest configuration"
          />

          <!-- Station ID -->
          <q-input
            filled
            v-model="formData.station_id"
            label="Station ID *"
            hint="Unique identifier for the monitoring station"
            :rules="[val => !!val || 'Valid station ID is required']"
          />

          <!-- Sync Settings -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">Synchronization Settings</div>

            <q-toggle
              v-model="formData.sync_enabled"
              label="Enable File Server Sync"
              color="primary"
              size="md"
            />

            <div class="q-mt-md">
              <q-input
                filled
                disable
                v-model.number="syncInterval"
                label="Sync Interval (minutes)"
                type="number"
                hint="Fixed interval for automatic synchronization"
              />
            </div>
          </q-card-section>

          <!-- Action Buttons -->
          <div class="row q-mt-lg">
            <q-space/>
            <div class="col-6">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                label="Save"
                class="full-width"
              />
            </div>
            <q-space/>
          </div>
        </q-form>
      </q-card-section>
    </q-card>


  </q-page>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {IngestExternalApiUbaCreate, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";
import {useIngestExternalApiUbaStore} from "stores/ingestExternalApiUbaStore";
import {useQuasar} from 'quasar'
import {useRouter} from "vue-router";


const store = useIngestExternalApiUbaStore()
const $q = useQuasar()
const router = useRouter()

const formData = ref<IngestExternalApiUbaUpdate>({
  name: '',
  project_id: null,
  description: '',
  station_id: null,
  sync_enabled: false
})
const syncInterval = ref(60)
const isLoading = ref(false)

const projectOptions = [
  {
    label: 'Project 1',
    id: 1
  }, {
    label: 'Project 2',
    id: 2
  }, {
    label: 'Project 3',
    id: 3
  }
]

async function save() {
  let data: IngestExternalApiUbaCreate = {
    name: formData.value.name,
    description: formData.value.description,
    project_id: formData.value.project_id,
    station_id: formData.value.station_id,
    sync_enabled: formData.value.sync_enabled
  }
  try {
    isLoading.value = true
    const result = await store.dispatchCreateIngestExternalApiDwd(data)
    $q.notify({
      position: "top",
      type: 'positive',
      message: 'Saved successfully'
    })

    // Navigate back to list
    await router.push(`/ingest/external-api-uba/${result.id}`)

  } catch (error) {
    $q.notify({
      position: "top",
      type: 'negative',
      message: 'Failed to create ingest'
    })
  } finally {
    isLoading.value = true
  }
}

</script>

<style scoped>

</style>
