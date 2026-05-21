<template>
  <q-list bordered separator class="rounded-borders">
    <q-expansion-item v-for="(item, i) in quality_control_functions" :key="i">
      <template #header>
        <q-item-section side>
          <q-icon
            v-if="removable"
            name="delete"
            color="red"
            @click.prevent="removeFunction(i)"
            class="cursor-pointer"
          />
        </q-item-section>
        <q-item-section>
          <div>{{ item.name }}</div>
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
        <q-space></q-space>
      </template>
      <q-list>
        <q-item v-for="(arg, j) in item.quality_control_function_arguments" :key="`${i}-${j}`">
          <q-item-section>
            <div v-if="isDatastreamType(arg)">
              {{ arg.name }}:
              <sta-datastream-selection-view :selected="arg.input.value" :default-opened="true" />
            </div>
          </q-item-section>
        </q-item>
      </q-list>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import { isDatastreamType } from 'src/utils/quality_control_utils';
import StaDatastreamSelectionView from 'components/StaDatastreamSelectionView.vue';
import type {
  QualityControlFunctionCreate,
  QualityControlFunctionPublic,
  QualityControlFunctionUpdate,
} from 'src/services/quality_control_setting/types';
import type { Datastream } from 'src/services/sta/types';

defineProps<{
  removable?: boolean;
  quality_control_functions:
    | QualityControlFunctionCreate[]
    | QualityControlFunctionPublic[]
    | QualityControlFunctionUpdate[];
}>();

const emit = defineEmits(['remove']);

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
</script>

<style scoped></style>
