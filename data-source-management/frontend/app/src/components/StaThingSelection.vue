<template>
  <q-select
    v-model="model"
    use-input
    fill-input
    hide-selected
    :options="options"
    option-label="name"
    @filter="loadOptions"
    label="Search Thing"
    dense
    outlined
    clearable
    hide-bottom-space
  >
    <template #after>
      <q-spinner-gears v-if="loading" size="16px" />
    </template>

    <template #no-option>
      <q-item>
        <q-item-section class="text-grey">No results</q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { debounce } from 'quasar';
import { useStaStore } from 'stores/staStore';
import { ref } from 'vue';
import type { StaEntity } from 'src/services/sta/types';

const model = defineModel<StaEntity | null>();
const { permission_group_id } = defineProps<{
  permission_group_id: number;
}>();

const staStore = useStaStore();
const loading = ref(false);
const options = ref<StaEntity[]>([]);

const loadOptions = debounce(async (val: string, update: (cb: () => void) => void) => {
  update(() => {
    loading.value = true;
  });

  try {
    const result = await staStore.dispatchFetchThings(permission_group_id, val);
    update(() => {
      options.value = result.value;
    });
  } catch {
    update(() => {
      options.value = [];
    });
  } finally {
    update(() => {
      loading.value = false;
    });
  }
}, 300);
</script>

<style scoped></style>
