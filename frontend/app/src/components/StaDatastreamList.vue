<template>
  <q-item dense class="q-px-sm q-py-xs">
    <q-item-section>
      <div class="row items-center q-gutter-x-sm q-gutter-y-xs text-body2" style="flex-wrap: wrap">
        <span>
          {{ displayDatastreamName }}
          <q-tooltip>{{ displayDatastreamName }}</q-tooltip>
        </span>

        <span v-if="!isCreatedDatastream(datastream)" class="text-grey-6">
          ID: {{ datastream['@iot.id'] }}
          <q-tooltip>ID</q-tooltip>
        </span>

        <span v-if="datastream.Thing?.name" class="text-grey-6 row items-center">
          <q-icon name="memory" size="14px" class="q-mr-xs" />
          {{ datastream.Thing.name }}
          <q-tooltip> Thing </q-tooltip>
        </span>

        <span v-if="datastream.alias" class="text-grey-6 row items-center">
          <q-icon name="tag" size="14px" class="q-mr-xs" />
          {{ datastream.alias }}
          <q-tooltip>Alias</q-tooltip>
        </span>

        <q-chip
          v-if="isCreatedDatastream(datastream)"
          outline
          color="orange"
          dense
          label="Created"
          size="sm"
        >
          <q-tooltip>Temporary Datastream</q-tooltip>
        </q-chip>
      </div>
    </q-item-section>

    <q-item-section side>
      <div class="row items-center">
        <q-btn
          v-if="datastream.alias"
          flat
          round
          icon="content_copy"
          size="xs"
          @click="copyClipboard(datastream.alias)"
        >
          <q-tooltip>Copy alias</q-tooltip>
        </q-btn>

        <q-btn
          v-if="!isCreatedDatastream(datastream) && !hideOpenButton"
          flat
          round
          icon="open_in_new"
          size="xs"
          :href="datastream['@iot.selfLink']"
          target="_blank"
        >
          <q-tooltip>Open</q-tooltip>
        </q-btn>

        <q-btn
          v-if="removable"
          flat
          round
          icon="delete_outline"
          color="negative"
          size="xs"
          @click="handleRemove"
        >
          <q-tooltip>Remove</q-tooltip>
        </q-btn>
      </div>
    </q-item-section>
  </q-item>
</template>
<script setup lang="ts">
import type { Datastream } from 'src/services/sta/types';
import { copyToClipboard, useQuasar } from 'quasar';
import { computed } from 'vue';

const props = defineProps<{
  datastream: Datastream;
  removable?: boolean | undefined;
  hideOpenButton?: boolean | undefined;
  hideThingName?: boolean | undefined;
}>();

const $q = useQuasar();

const emit = defineEmits<{
  (e: 'remove', datastream: Datastream): void;
}>();

function isCreatedDatastream(ds: Datastream) {
  return ds['@iot.id'] === null && ds['@iot.selfLink'] === null;
}

const copyClipboard = (text: string | null) => {
  if (!text) {
    return;
  }

  copyToClipboard(text)
    .then(() => {
      $q.notify({
        message: 'Copied to clipboard',
        color: 'positive',
        icon: 'check',
      });
    })
    .catch(() => {
      $q.notify({
        message: 'Failed to copy',
        color: 'negative',
        icon: 'error',
      });
    });
};

const displayDatastreamName = computed(() => {
  const name = props.datastream.name ?? '';
  const thingName = props.datastream.Thing?.name ?? '';

  if (!props.hideThingName || !thingName) {
    return name;
  }

  const escapedThing = thingName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  return name.replace(new RegExp(`^${escapedThing}[\\s\\-:/|]*`, 'i'), '').trim();
});

function handleRemove() {
  emit('remove', props.datastream);
}
</script>

<style scoped></style>
