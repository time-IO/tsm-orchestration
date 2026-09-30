<template>
  <div>
    <template v-if="endpointStore.loading">
      <q-item v-for="n in 3" :key="n" style="max-width: 300px">
        <q-item-section avatar>
          <q-skeleton type="QAvatar" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            <q-skeleton type="text" />
          </q-item-label>
          <q-item-label caption>
            <q-skeleton type="text" width="65%" />
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>

    <template v-else-if="endpointStore.endpoints.length">
      <q-list bordered separator>
        <q-item
          v-for="endpoint in endpointStore.endpoints"
          :key="endpoint.name"
          clickable
          tag="a"
          :href="endpoint.url"
          target="_blank"
          rel="noopener noreferrer"
        >
          <q-item-section avatar>
            <q-icon name="storage" color="primary" />
          </q-item-section>

          <q-item-section>
            <q-item-label>
              {{ endpoint.displayName }}
              <q-badge v-if="endpoint.is_own" color="positive" class="q-ml-sm">
                Your project
              </q-badge>
            </q-item-label>
            <q-item-label caption>{{ endpoint.url }}</q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-icon name="launch" />
          </q-item-section>
        </q-item>
      </q-list>
    </template>

    <q-banner v-else class="bg-grey-2"> No FROST endpoints available. </q-banner>
  </div>
</template>

<script setup lang="ts">
import { useEndpointStore } from '@/stores/endpointStore';

const endpointStore = useEndpointStore();
</script>
