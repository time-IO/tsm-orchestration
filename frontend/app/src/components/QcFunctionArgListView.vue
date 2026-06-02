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
          <div class="text-weight-medium text-subtitle1">{{ item.name }}</div>
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

      <q-list dense>
        <template v-for="(arg, j) in item.quality_control_function_arguments" :key="`${i}-${j}`">
          <q-item v-if="isDatastreamType(arg)">
            <q-item-section>
              <q-card flat bordered class="q-mb-sm">
                <!-- Header -->
                <q-card-section
                  class="row items-center q-py-xs q-px-sm"
                  style="background-color: #e4eaed"
                >
                  <div class="text-weight-medium text-capitalize">
                    {{ arg.name }}
                  </div>
                  <q-space />

                  <q-btn
                    v-if="removable"
                    flat
                    dense
                    icon="add"
                    label="Add Datastream"
                    size="sm"
                    @click.stop="
                      () => {
                        onAddDatastream(i, j);
                      }
                    "
                  />
                </q-card-section>
                <q-card-section class="q-pa-sm">
                  <sta-datastream-selection-view
                    :selected="arg.input.value"
                    :default-opened="true"
                    :removable="removable === true"
                    :hide-thing-name="true"
                    @remove="removeDatastream(i, j, $event)"
                  />
                </q-card-section>
              </q-card>
            </q-item-section>
          </q-item>
        </template>
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
  expandAll?: boolean;
  quality_control_functions:
    | QualityControlFunctionCreate[]
    | QualityControlFunctionPublic[]
    | QualityControlFunctionUpdate[];
}>();

const emit = defineEmits(['remove', 'remove-datastream', 'add-datastream']);

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
</script>

<style scoped></style>
