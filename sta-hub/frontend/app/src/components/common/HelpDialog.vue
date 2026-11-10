<template>
  <q-btn
    flat
    round
    dense
    size="xs"
    icon="help_outline"
    color="grey-7"
    :aria-label="title"
    @click="open = true"
  >
    <q-tooltip>{{ title }}</q-tooltip>
  </q-btn>

  <q-dialog v-model="open">
    <q-card class="help-dialog">
      <q-card-section class="row items-center no-wrap">
        <div class="col text-body1 text-weight-bold">{{ title }}</div>
        <q-btn v-close-popup flat round dense icon="close" aria-label="Close" />
      </q-card-section>

      <q-card-section class="q-pt-none">
        <slot />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{ title: string }>();

const open = ref(false);
</script>

<style scoped>
.help-dialog {
  width: 600px;
  max-width: 90vw;
}
</style>
