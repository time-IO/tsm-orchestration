<template>
  <q-select
    filled
    v-model="localValue"
    :options="filteredOptions"
    @filter="filterPermissionGroup"
    label="Permission Group *"
    option-value="id"
    option-label="name"
    emit-value
    map-options
    clearable
    use-input
    hint="Select the permission group this ingest belongs to"
    :rules="rules"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import { QSelect, useQuasar } from 'quasar';
import type { PermissionGroup } from 'src/services/permission_group/types';

const $q = useQuasar();

const props = defineProps<{
  modelValue: number | null | undefined;
  rules?: Array<(val: unknown) => string | boolean>;
}>();

defineEmits<{
  (e: 'update:modelValue', value: number | null): void;
}>();

const permissionGroupStore = usePermissionGroupStore();
const localValue = ref<number | null | undefined>(props.modelValue);
const filteredOptions = ref<PermissionGroup[]>([]);

// Load permission groups on mount
onMounted(async () => {
  try {
    await permissionGroupStore.dispatchGetList();
    filteredOptions.value = [...permissionGroupStore.permissionGroups];
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch permission groups',
    });
  }
});

// Sync localValue when prop changes (e.g., reset)
watch(
  () => props.modelValue,
  (val) => {
    localValue.value = val;
  },
);

// Filter logic (same as in original page)
function filterPermissionGroup(
  val: string,
  update: (fn: () => void, cb?: (ref: QSelect) => void) => void,
) {
  if (val === '') {
    update(() => {
      filteredOptions.value = [...permissionGroupStore.permissionGroups];
    });
    return;
  }

  update(
    () => {
      const needle = val.toLowerCase();
      filteredOptions.value = permissionGroupStore.permissionGroups.filter((v) =>
        v.name.toLowerCase().includes(needle),
      );
    },
    (ref: QSelect) => {
      // this is used to select the option if you hit enter
      if (val !== '' && ref.options && ref.options.length > 0) {
        ref.setOptionIndex(-1); // reset optionIndex in case there is something selected
        ref.moveOptionSelection(1, true); // focus the first selectable option and do not update the input-value
      }
    },
  );
}
</script>

<style scoped></style>
