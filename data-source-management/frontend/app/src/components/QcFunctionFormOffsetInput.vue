<template>
  <q-input
    filled
    v-model="model"
    :label="`${label} (enter a offset alias)`"
    :rules="rules"
    :hint="hint"
    v-bind="$attrs"
  >
    <template v-slot:append>
      <q-btn round flat icon="help_outline" @click="showDocs">
        <q-tooltip> View Pandas Docs for information on available offset aliases </q-tooltip>
      </q-btn>
    </template>
    <template v-slot:after>
      <slot name="after"></slot>
    </template>
  </q-input>
</template>

<script setup lang="ts">
import type { ValidationRule } from 'quasar';

const model = defineModel<number | null>({ default: null });

defineProps<{
  rules: Array<ValidationRule>;
  label: string;
  hint: string;
}>();

const showDocs = () => {
  window.open(
    'https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases',
    '_blank',
  );
};
</script>

<style scoped></style>
