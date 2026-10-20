<template>
  <q-markup-table flat separator="horizontal" class="endpoint-url-table">
    <tbody>
      <tr v-for="link in urls" :key="link.label">
        <td class="endpoint-url-table__label">
          {{ link.label }}
        </td>
        <td>
          <div class="ellipsis">
            {{ link.url }}
            <q-tooltip>{{ link.url }}</q-tooltip>
          </div>
        </td>
        <td class="endpoint-url-table__action">
          <copy-button size="sm" :text="link.url" />
        </td>
        <td class="endpoint-url-table__action">
          <open-in-new-tab-button size="sm" :href="link.url" :disabled-hint="link.hint" />
        </td>
      </tr>
    </tbody>
  </q-markup-table>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import CopyButton from '@/components/common/CopyButton.vue';
import OpenInNewTabButton from '@/components/common/OpenInNewTabButton.vue';
import type { FrostEndpoint } from '@/services/endpoints/types';

const props = defineProps<{ endpoint: FrostEndpoint }>();

const urls = computed(() => [
  { label: 'Automatic', url: props.endpoint.url, hint: null },
  { label: 'Public', url: props.endpoint.public_url, hint: null },
  {
    label: 'Internal',
    url: props.endpoint.internal_url,
    hint: props.endpoint.is_internal
      ? null
      : 'Not accessible: Requires membership in the permission group of this endpoint.',
  },
]);
</script>

<style scoped>
.endpoint-url-table :deep(table) {
  table-layout: fixed;
  width: 100%;
}

.endpoint-url-table td {
  padding-left: 0;
}

.endpoint-url-table__label {
  width: 90px;
}

.endpoint-url-table__action {
  width: 40px;
  padding-right: 0;
}
</style>
