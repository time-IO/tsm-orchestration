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
        :selected="selected"
        :default-opened="true"
        :removable="removable"
        :hide-thing-name="hideThingName"
        :hide-open-button="hideOpenButton"
        @remove="(ds) => emit('remove', ds)"
      />
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import StaDatastreamSelectionView from '@/components/StaDatastreamSelectionView.vue';
import type { Datastream } from '@/services/sta/types';

const {
  label,
  selected,
  removable = false,
  addable = false,
  hideThingName = false,
  hideOpenButton = false,
} = defineProps<{
  label: string;
  selected: Datastream[];
  removable?: boolean;
  addable?: boolean;
  hideThingName?: boolean;
  hideOpenButton?: boolean;
}>();

const emit = defineEmits<{
  (e: 'add'): void;
  (e: 'remove', datastream: Datastream): void;
}>();
</script>

<style scoped></style>
