<template>
  <q-card flat bordered>
    <q-expansion-item v-model="expanded" dense header-class="q-pl-sm">
      <template #header>
        <q-item-section>
          <span class="text-weight-medium text-grey-9">{{ thingName }}</span>
        </q-item-section>
        <q-item-section side>
          <q-chip dense color="blue-grey-3" text-color="white">
            {{ datastreams.length }}
          </q-chip>
        </q-item-section>
      </template>

      <q-separator />
      <q-list dense separator>
        <sta-datastream-list
          v-for="(ds, index) in datastreams"
          :key="ds['@iot.id'] ?? `created-${index}`"
          :datastream="ds"
          :removable="removable"
          :hide-thing-name="hideThingName"
          :hide-open-button="hideOpenButton"
          @remove="(datastream) => emit('remove', datastream)"
        />
      </q-list>
    </q-expansion-item>
  </q-card>
</template>

<script setup lang="ts">
import StaDatastreamList from '@/components/StaDatastreamList.vue';
import type { Datastream } from '@/services/sta/types';

const expanded = defineModel<boolean>('expanded', { default: true });

const {
  thingName,
  datastreams,
  removable = false,
  hideThingName = false,
  hideOpenButton = false,
} = defineProps<{
  thingName: string;
  datastreams: Datastream[];
  removable?: boolean;
  hideThingName?: boolean;
  hideOpenButton?: boolean;
}>();

const emit = defineEmits<{
  (e: 'remove', datastream: Datastream): void;
}>();
</script>
