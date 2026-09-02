<template>
  <q-btn
    v-bind="$attrs"
    flat
    round
    icon="content_copy"
    size="sm"
    @click="copyClipboard(textToCopy)"
  >
    <q-tooltip>{{ title }}</q-tooltip>
  </q-btn>
</template>

<script setup lang="ts">
import { copyToClipboard, useQuasar } from 'quasar';

const $q = useQuasar();

defineProps<{
  title: string;
  textToCopy: string | null;
}>();

const copyClipboard = (dataToCopy: string | null) => {
  if (!dataToCopy) {
    return;
  }

  copyToClipboard(dataToCopy)
    .then(() => {
      $q.notify({
        message: 'Copied to clipboard',
        color: 'positive',
        icon: 'check',
      });
    })
    .catch(() => {
      $q.notify({
        message: 'Failed to copy',
        color: 'negative',
        icon: 'error',
      });
    });
};
</script>

<style scoped></style>
