<template>
  <draggable
    v-model="localFunctions"
    item-key="_clientId"
    handle=".drag-handle"
    :disabled="!removable"
    ghost-class="drag-ghost"
    @change="onReorder"
  >
    <template #item="{ element: item, index: i }">
      <q-list separator class="rounded-borders q-mt-sm q-ml-sm">
        <q-expansion-item
          :model-value="expandAll ?? false"
          style="border: 1px solid #cfd8dc; border-radius: 4px"
          class="q-mb-md"
        >
          <template #header>
            <q-item-section v-if="removable" side class="q-pr-none">
              <q-icon
                name="drag_indicator"
                size="1.4em"
                class="drag-handle cursor-move text-grey-6"
                @click.stop
              />
            </q-item-section>

            <q-item-section>
              <div class="text-weight-medium text-subtitle1">
                {{ item.name }}
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
                  v-if="nonDatastreamArgs(item).length > 0"
                  class="text-blue-9 q-mx-xs"
                >
                  |
                </span>
                {{
                  nonDatastreamArgs(item)
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
            <template
              v-for="(arg, j) in item.quality_control_function_arguments"
              :key="`${item._clientId}-${j}`"
            >
              <q-item v-if="isDatastreamType(arg)">
                <q-item-section>
                  <sta-datastream-card
                    :label="arg.name"
                    :selected="arg.input.value"
                    :removable="removable === true"
                    :addable="removable === true"
                    :hide-thing-name="true"
                    @add="onAddDatastream(i, Number(j))"
                    @remove="removeDatastream(i, Number(j), $event)"
                  />
                </q-item-section>
              </q-item>
            </template>
          </q-list>
        </q-expansion-item>
      </q-list>
    </template>
  </draggable>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import draggable from 'vuedraggable';
import { isDatastreamType } from 'src/utils/quality_control_utils';
import StaDatastreamCard from 'components/StaDatastreamCard.vue';
import type {
  QualityControlFunctionCreate,
  QualityControlFunctionPublic,
  QualityControlFunctionUpdate,
  QualityControlFunctionArgumentCreate,
  QualityControlFunctionArgumentPublic,
} from 'src/services/quality_control_setting/types';
import type { Datastream } from 'src/services/sta/types';

type FunctionWithClientId = (
  | QualityControlFunctionCreate
  | QualityControlFunctionPublic
  | QualityControlFunctionUpdate
) & { _clientId: string };

type QcFunctionArgument =
  | QualityControlFunctionArgumentCreate
  | QualityControlFunctionArgumentPublic



const props = defineProps<{
  removable?: boolean;
  expandAll?: boolean;
  quality_control_functions:
    | QualityControlFunctionCreate[]
    | QualityControlFunctionPublic[]
    | QualityControlFunctionUpdate[];
}>();

const emit = defineEmits([
  'remove',
  'remove-datastream',
  'add-datastream',
  'edit',
  'reorder',
]);

// vuedraggable needs a stable, unique key per item to correctly track
// elements while dragging. Real entities have a numeric `id`; functions
// that were only just added client-side (not yet saved) don't, so we
// fall back to a generated one. This is purely a rendering aid and is
// never sent to the backend.
const localFunctions = computed<FunctionWithClientId[]>({
  get() {
    return props.quality_control_functions.map((item) => ({
      ...item,
      _clientId:
        '_clientId' in item && item._clientId
          ? item._clientId
          : 'id' in item && item.id != null
            ? `id-${item.id}`
            : `unstable-${item.name}`,
    }));
  },
  set() {
    // dragging is handled via the @change event below, since we need
    // the *previous* and *new* index to tell the parent how to reorder
    // its own array (see onReorder). Writes through this setter are
    // intentionally ignored.
  },
});

function onReorder(event: { moved?: { oldIndex: number; newIndex: number } }) {
  if (!event.moved) return;
  emit('reorder', { oldIndex: event.moved.oldIndex, newIndex: event.moved.newIndex });
}

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

function nonDatastreamArgs(item: FunctionWithClientId) {
  return item.quality_control_function_arguments.filter((a: QcFunctionArgument) => !isDatastreamType(a));
}
</script>

<style scoped>
.drag-ghost {
  opacity: 0.4;
}
</style>
