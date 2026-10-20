<template>
  <div class="q-pa-lg">
    <div class="row items-center no-wrap q-mb-lg">
      <div class="col text-body1 text-weight-bold ellipsis">{{ endpoint.display_name }}</div>
      <q-btn flat round dense icon="close" aria-label="Close" @click="emit('close')" />
    </div>

    <q-list class="q-mb-lg">
      <q-item class="q-px-none q-mb-sm">
        <q-item-section>
          <q-item-label caption>
            Access
            <visibility-help />
          </q-item-label>
          <q-item-label class="row items-center no-wrap">
            <visibility-badge :visibility="visibility" />
            <open-in-new-tab-button
              dense
              :round="false"
              size="md"
              :color="VISIBILITIES[visibility].color"
              class="q-ml-sm"
              :href="endpoint.url"
            />
          </q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none q-mb-sm">
        <q-item-section>
          <q-item-label caption>Full name</q-item-label>
          <q-item-label class="endpoint-info__value">{{ endpoint.name }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none q-mb-sm">
        <q-item-section>
          <q-item-label caption>Display name</q-item-label>
          <q-item-label>{{ endpoint.display_name }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none q-mb-sm">
        <q-item-section>
          <q-item-label caption>
            URL
            <url-help />
          </q-item-label>
          <endpoint-url-table :endpoint="endpoint" />
        </q-item-section>
      </q-item>
    </q-list>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import OpenInNewTabButton from '@/components/common/OpenInNewTabButton.vue';
import VisibilityBadge from '@/components/common/VisibilityBadge.vue';
import EndpointUrlTable from '@/components/EndpointUrlTable.vue';
import UrlHelp from '@/components/UrlHelp.vue';
import VisibilityHelp from '@/components/VisibilityHelp.vue';
import type { FrostEndpoint } from '@/services/endpoints/types';
import { endpointVisibility, VISIBILITIES } from '@/utils/visibility';

const props = defineProps<{ endpoint: FrostEndpoint }>();
const emit = defineEmits<{ close: [] }>();

const visibility = computed(() => endpointVisibility(props.endpoint));
</script>

<style scoped>
.endpoint-info__value {
  word-break: break-all;
}
</style>
