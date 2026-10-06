<template>
  <q-list ref="listRef" separator class="rounded-borders q-mt-sm q-ml-sm">
    <q-expansion-item
      v-for="(item, i) in localFunctions"
      :key="item._clientId"
      :model-value="expandAll ?? false"
      style="border: 1px solid #cfd8dc; border-radius: 4px"
      class="q-mb-md"
    >
      <template #header>
        <q-item-section v-if="removable" side class="q-pr-none">
          <div class="column items-center">
            <q-btn
              flat
              round
              dense
              size="sm"
              icon="arrow_upward"
              :disable="i === 0"
              aria-label="Move function up"
              @click.stop="moveUp(i)"
            />
            <q-icon
              name="drag_indicator"
              size="1.4em"
              class="drag-handle cursor-move text-grey-6"
              @click.stop
            />
            <q-btn
              flat
              round
              dense
              size="sm"
              icon="arrow_downward"
              :disable="i === localFunctions.length - 1"
              aria-label="Move function down"
              @click.stop="moveDown(i)"
            />
          </div>
        </q-item-section>

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
            <span v-if="nonDatastreamArgs(item).length > 0" class="text-blue-9 q-mx-xs"> | </span>
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

<script setup lang="ts">
import { isDatastreamType } from '@/utils/quality_control_utils';
import StaDatastreamCard from '@/components/StaDatastreamCard.vue';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import Sortable from 'sortablejs';
import type {
  QualityControlFunctionCreate,
  QualityControlFunctionPublic,
  QualityControlFunctionUpdate,
  QualityControlFunctionArgumentCreate,
  QualityControlFunctionArgumentPublic,
} from '@/services/quality_control_setting/types';
import type { Datastream } from '@/services/sta/types';

type FunctionWithClientId = (
  QualityControlFunctionCreate | QualityControlFunctionPublic | QualityControlFunctionUpdate
) & { _clientId: string };

type QcFunctionArgument =
  QualityControlFunctionArgumentCreate | QualityControlFunctionArgumentPublic;

const props = defineProps<{
  removable?: boolean;
  expandAll?: boolean;
  quality_control_functions:
    | QualityControlFunctionCreate[]
    | QualityControlFunctionPublic[]
    | QualityControlFunctionUpdate[];
}>();

const emit = defineEmits(['remove', 'remove-datastream', 'add-datastream', 'edit', 'reorder']);

const localFunctions = computed<FunctionWithClientId[]>(() => {
  return props.quality_control_functions.map((item) => ({
    ...item,
    _clientId:
      '_clientId' in item && item._clientId
        ? item._clientId
        : 'id' in item && item.id != null
          ? `id-${item.id}`
          : `unstable-${item.name}`,
  }));
});

const listRef = ref<{ $el: HTMLElement } | HTMLElement | null>(null);
let sortable: Sortable | null = null;

function resolveListEl(): HTMLElement | null {
  const el = listRef.value as unknown;
  if (!el) return null;
  return (el as { $el?: HTMLElement }).$el ?? (el as HTMLElement);
}

function initSortable() {
  const el = resolveListEl();
  if (!el || !removable.value) return;
  sortable = new Sortable(el, {
    handle: '.drag-handle',
    animation: 150,
    onEnd(evt) {
      const oldIndex = evt.oldIndex;
      const newIndex = evt.newIndex;
      if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return;
      emit('reorder', { oldIndex, newIndex });
    },
  });
}

const removable = computed(() => props.removable ?? false);

onMounted(initSortable);

watch(removable, (val) => {
  if (val && !sortable) initSortable();
  if (!val && sortable) {
    sortable.destroy();
    sortable = null;
  }
});

onBeforeUnmount(() => {
  sortable?.destroy();
  sortable = null;
});

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
  return item.quality_control_function_arguments.filter(
    (a: QcFunctionArgument) => !isDatastreamType(a),
  );
}

function moveUp(index: number) {
  if (index === 0) return;
  emit('reorder', { oldIndex: index, newIndex: index - 1 });
}

function moveDown(index: number) {
  if (index === localFunctions.value.length - 1) return;
  emit('reorder', { oldIndex: index, newIndex: index + 1 });
}
</script>

<style scoped>
.drag-ghost {
  opacity: 0.4;
}
</style>
