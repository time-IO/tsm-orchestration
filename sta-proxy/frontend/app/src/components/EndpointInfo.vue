<template>
  <div class="q-pa-lg">
    <div class="row items-center no-wrap q-mb-lg">
      <div class="col text-body1 text-weight-bold ellipsis">{{ endpoint.display_name }}</div>
      <q-btn flat round dense icon="close" aria-label="Close" @click="emit('close')" />
    </div>

    <q-list class="q-mb-lg">
      <q-item class="q-px-none">
        <q-item-section>
          <q-item-label caption>Access</q-item-label>
          <q-item-label>
            <visibility-badge :visibility="visibility" />
          </q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none">
        <q-item-section>
          <q-item-label caption>Full name</q-item-label>
          <q-item-label class="endpoint-info__value">{{ endpoint.name }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none">
        <q-item-section>
          <q-item-label caption>Display name</q-item-label>
          <q-item-label>{{ endpoint.display_name }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-item class="q-px-none">
        <q-item-section>
          <q-item-label caption>URL</q-item-label>
          <q-item-label class="endpoint-info__value"
            >{{ endpoint.url }}
            <copy-button size="xs" :text="endpoint.url" />
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <div class="row q-gutter-sm">
      <q-btn
        unelevated
        no-caps
        color="primary"
        icon="open_in_new"
        label="Open"
        :href="endpoint.url"
        target="_blank"
        rel="noopener noreferrer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import VisibilityBadge from '@/components/common/VisibilityBadge.vue';
import CopyButton from '@/components/common/CopyButton.vue';
import type { FrostEndpoint } from '@/services/endpoints/types';
import { endpointVisibility } from '@/utils/visibility';

const props = defineProps<{ endpoint: FrostEndpoint }>();
const emit = defineEmits<{ close: [] }>();

const visibility = computed(() => endpointVisibility(props.endpoint));
</script>

<style scoped>
.endpoint-info__value {
  word-break: break-all;
}
</style>
