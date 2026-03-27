import { defineStore } from 'pinia';
import { ref } from 'vue';

interface ExternalApiRow {
  id: number;
  name: string;
  permission_group: { name: string };
  provider: string;
}

export const useIngestTriggerSelectionStore = defineStore('ingestTriggerSelection', () => {
  const selected = ref<ExternalApiRow[]>([]);

  function clear() {
    selected.value = [];
  }

  const ingestName = ref<string>('');
  return { selected, ingestName, clear };
});
