<template>
  <div class="q-pa-xs flex-shrink-0 q-mb-sm" style="width: 200px">
    <q-card flat bordered class="q-pa-sm full-width">
      <q-card-section class="q-pa-none">
        <div class="row items-center justify-between no-wrap">
          <div class="col ellipsis">
            <span class="text-body1">
              {{ datastream.name }}
              <q-tooltip>{{ datastream.name }}</q-tooltip>
            </span>

            <span v-if="!isCreatedDatastream(datastream)" class="text-caption text-grey-6 q-ml-xs">
              (ID: {{ datastream['@iot.id'] }})
            </span>
          </div>

          <q-chip
            v-if="isCreatedDatastream(datastream)"
            outline
            color="orange"
            dense
            label="Created"
            class="q-ml-xs"
            size="sm"
          >
            <q-tooltip>Temporary Datastream</q-tooltip>
          </q-chip>
        </div>

        <div class="q-mt-sm column text-caption text-grey-7">
          <div class="row items-center q-mb-xs" v-if="datastream.Thing?.name">
            <q-icon name="memory" size="14px" class="q-mr-xs">
              <q-tooltip>Thing</q-tooltip>
            </q-icon>
            <span>{{ truncateText(datastream.Thing.name, 24) }}</span>
          </div>

          <div class="row items-center q-mb-xs" v-if="datastream.alias">
            <q-icon name="tag" size="14px" class="q-mr-xs">
              <q-tooltip>Alias</q-tooltip>
            </q-icon>
            {{ truncateText(datastream.alias, 12) }}
            <q-btn
              flat
              round
              icon="content_copy"
              size="sm"
              @click="copyClipboard(datastream.alias)"
              title="Copy alias"
            />
          </div>
        </div>

        <div class="row justify-end no-wrap q-mt-sm">
          <q-btn
            v-if="!isCreatedDatastream(datastream) && !hideOpenButton"
            dense
            flat
            round
            icon="open_in_new"
            :href="datastream['@iot.selfLink']"
            target="_blank"
            size="sm"
          >
            <q-tooltip>Open</q-tooltip>
          </q-btn>

          <q-btn
            v-if="removable"
            dense
            flat
            round
            icon="delete_outline"
            color="negative"
            @click="handleRemove"
            class="q-ml-sm"
            size="sm"
          >
            <q-tooltip>Remove</q-tooltip>
          </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>
<script setup lang="ts">
import type { Datastream } from 'src/services/sta/types';
import { truncateText } from 'src/utils/string_utils';
import { copyToClipboard, useQuasar } from 'quasar';

const props = defineProps<{
  datastream: Datastream;
  removable?: boolean;
  hideOpenButton?: boolean | undefined;
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

function handleRemove() {
  emit('remove', props.datastream);
}
</script>

<style scoped></style>
