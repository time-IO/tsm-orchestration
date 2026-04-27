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
          {{ item.name }}
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
            <div v-else>
              <q-field :label="arg.name" filled stack-label>
                <template v-slot:control>
                  <div class="self-center full-width no-outline">
                    {{ arg.input.value }}
                  </div>
                </template>
              </q-field>
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
</script>

<style scoped></style>
