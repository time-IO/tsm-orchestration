<template>
  <q-card flat bordered class="q-mb-sm">
    <q-card-section class="row items-center q-py-xs q-px-sm" style="background-color: #e4eaed">
      <div class="text-weight-medium text-capitalize text-grey-9">
        {{ label }}
      </div>
      <q-space />
      <q-btn
        v-if="addable"
        flat
        dense
        icon="add"
        label="Add Datastream"
        size="sm"
        @click.stop="emit('add')"
      />
    </q-card-section>
    <q-card-section class="q-pa-sm">
      <sta-datastream-selection-view
        :selected="props.selected"
        :default-opened="true"
        :removable="props.removable"
        :hide-thing-name="props.hideThingName"
        :hide-open-button="props.hideOpenButton"
        @remove="(ds) => emit('remove', ds)"
      />
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import StaDatastreamSelectionView from 'components/StaDatastreamSelectionView.vue';
import type { Datastream } from 'src/services/sta/types';

const props = withDefaults(
  defineProps<{
    label: string;
    selected: Datastream[];
    removable?: boolean;
    addable?: boolean;
    hideThingName?: boolean;
    hideOpenButton?: boolean;
  }>(),
  {
    removable: false,
    addable: false,
    hideThingName: false,
    hideOpenButton: false,
  },
);

const emit = defineEmits<{
  (e: 'add'): void;
  (e: 'remove', datastream: Datastream): void;
}>();
</script>

<style scoped></style>
