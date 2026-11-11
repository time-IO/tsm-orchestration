<template>
  <q-btn ref="button" flat round icon="content_copy" aria-label="Copy to clipboard" />
</template>

<script setup lang="ts">
import { useTemplateRef } from 'vue';
import { useCopy } from '@/composables/useCopy';

const props = defineProps<{ text: string }>();

useCopy(useTemplateRef('button'), () => props.text);
</script>
