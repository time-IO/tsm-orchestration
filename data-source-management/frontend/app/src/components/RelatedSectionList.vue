<template>
  <div>
    <div v-if="$slots.description" class="text-caption text-grey-7 q-mb-md">
      <slot name="description" />
    </div>

    <q-list v-if="items.length" bordered separator class="rounded-borders">
      <q-item v-for="(item, index) in items" :key="item.url ?? item.label ?? index">
        <slot name="item" :item="item" :index="index">
          <q-item-section>
            <q-item-label class="text-subtitle2 text-weight-medium">{{ item.label }}</q-item-label>
          </q-item-section>

          <q-item-section v-if="item.url" side>
            <q-btn
              flat
              round
              dense
              icon="open_in_new"
              color="grey-7"
              @click="openInNewTab(item.url)"
            >
              <q-tooltip>Open in new tab</q-tooltip>
            </q-btn>
          </q-item-section>
        </slot>
      </q-item>
    </q-list>

    <div v-else class="text-caption text-grey-6">
      <slot name="empty">{{ emptyLabel }}</slot>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends { label: string; url?: string }">
const { items, emptyLabel = 'Nothing related yet.' } = defineProps<{
  items: T[];
  emptyLabel?: string;
}>();

defineSlots<{
  /** Text above the list. */
  description?: () => unknown;
  /** One row. Falls back to name + "open in new tab" button. */
  item?: (props: { item: T; index: number }) => unknown;
  /** Shown instead of the list when `items` is empty. */
  empty?: () => unknown;
}>();

function openInNewTab(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer');
}
</script>
