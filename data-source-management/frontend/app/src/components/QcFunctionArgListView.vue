<template>
  <q-list separator class="rounded-borders q-mt-sm q-ml-sm">
    <q-expansion-item
      v-for="(item, i) in quality_control_functions"
      :key="i"
      :model-value="expandAll ?? false"
      style="border: 1px solid #cfd8dc; border-radius: 4px"
      class="q-mb-md"
    >
      <template #header>
        <q-item-section>
          <div class="text-weight-medium text-subtitle1">
            {{ item.name }}
            <span v-if="item.label" class="text-h7 text-blue-grey-6">— {{ item.label }}</span>
          </div>
          <div class="text-caption text-grey-6">
            <template v-if="getAlias(item, 'field').length">
              Field: {{ getAlias(item, 'field').join(', ') }}
            </template>

            <template v-if="getAlias(item, 'target', getAlias(item, 'field')).length">
              <span class="text-blue-9 q-mx-xs"> | </span>
              Target: {{ getAlias(item, 'target', getAlias(item, 'field')).join(', ') }}
            </template>
            <span
              v-if="
                item.quality_control_function_arguments.filter((a) => !isDatastreamType(a)).length >
                0
              "
              class="text-blue-9 q-mx-xs"
            >
              |
            </span>
            {{
              item.quality_control_function_arguments
                .filter((a) => !isDatastreamType(a))
                .map((a) => `${a.name}: ${a.input.value}`)
                .join(' | ')
            }}
          </div>
        </q-item-section>
        <q-space />

        <q-item-section side class="q-pl-none">
          <div class="row items-center no-wrap q-gutter-sm">
            <q-icon
              v-if="removable"
              name="delete"
              color="red"
              size="1.6em"
              @click.prevent="removeFunction(i)"
              class="cursor-pointer"
            />
            <q-icon
              v-if="removable"
              name="edit"
              color="primary"
              size="1.6em"
              @click.prevent="editFunction(i)"
              class="cursor-pointer q-mr-sm"
            />
          </div>
        </q-item-section>
      </template>

      <q-list dense>
        <template v-for="(arg, j) in item.quality_control_function_arguments" :key="`${i}-${j}`">
          <q-item v-if="isDatastreamType(arg)">
            <q-item-section>
              <sta-datastream-card
                :label="arg.name"
                :selected="arg.input.value"
                :removable="removable === true"
                :addable="removable === true"
                :hide-thing-name="true"
                @add="onAddDatastream(i, j)"
                @remove="removeDatastream(i, j, $event)"
              />
            </q-item-section>
          </q-item>
        </template>
      </q-list>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import { isDatastreamType } from 'src/utils/quality_control_utils';
import StaDatastreamCard from 'components/StaDatastreamCard.vue';
import type {
  QualityControlFunctionCreate,
  QualityControlFunctionPublic,
  QualityControlFunctionUpdate,
} from 'src/services/quality_control_setting/types';
import type { Datastream } from 'src/services/sta/types';

defineProps<{
  removable?: boolean;
  expandAll?: boolean;
  quality_control_functions:
    | QualityControlFunctionCreate[]
    | QualityControlFunctionPublic[]
    | QualityControlFunctionUpdate[];
}>();

const emit = defineEmits(['remove', 'remove-datastream', 'add-datastream', 'edit']);

function removeFunction(index: number | string) {
  emit('remove', index);
}

function getAlias(
  item: QualityControlFunctionCreate | QualityControlFunctionPublic | QualityControlFunctionUpdate,
  name: string,
  alreadyShown: string[] = [],
): string[] {
  const datastreamArg = item.quality_control_function_arguments.find(
    (a) => isDatastreamType(a) && a.name === name,
  );
  if (!datastreamArg) return [];
  return (datastreamArg.input.value as Datastream[])
    .map((ds) => ds.alias)
    .filter((alias): alias is string => alias != null && !alreadyShown.includes(alias));
}

function removeDatastream(funcIndex: number, argIndex: number, datastream: Datastream) {
  emit('remove-datastream', { funcIndex, argIndex, datastream });
}

function onAddDatastream(funcIndex: number, argIndex: number) {
  emit('add-datastream', { funcIndex, argIndex });
}
function editFunction(index: number) {
  emit('edit', index);
}
</script>

<style scoped></style>
