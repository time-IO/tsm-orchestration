<template>
  <q-dialog v-model="showDialog">
    <q-card style="width: 50vw; max-width: 80vw">
      <q-card-section class="row items-start no-wrap q-pb-none">
        <div class="col">
          <div class="text-h6">{{ title }}</div>
          <div v-if="subtitle" class="text-caption text-grey-7">{{ subtitle }}</div>
        </div>
        <copy-button v-if="content" :text="content" size="sm" text-color="grey" />
        <q-btn v-close-popup dense flat round icon="close" />
      </q-card-section>
      <q-card-section>
        <pre class="json-content">{{ formattedContent }}</pre>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import CopyButton from '@/components/common/CopyButton.vue';

const showDialog = defineModel<boolean>({ default: false });
const { title, subtitle, content } = defineProps<{
  title: string;
  subtitle?: string | undefined;
  content: string | null;
}>();

const formattedContent = computed(() => {
  const text = content ?? '';
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
});
</script>

<style scoped>
.json-content {
  margin: 0;
  max-height: 60vh;
  overflow: auto;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
