<template>
  <q-banner class="expandable-banner" :class="style.banner">
    <template #avatar>
      <q-icon :name="style.icon" />
    </template>
    <q-expansion-item
      v-if="slots.default && expandable"
      :default-opened="defaultOpened"
      dense-toggle
      :label="title"
      :header-class="['q-pa-none', titleClass]"
      header-style="min-height: 40px"
      :expand-icon-class="style.text"
    >
      <div class="expandable-banner__description scroll-y q-pt-sm">
        <slot />
      </div>
    </q-expansion-item>
    <template v-else>
      <div class="row items-center" :class="titleClass" style="min-height: 40px">
        {{ title }}
      </div>
      <div v-if="slots.default" class="expandable-banner__description scroll-y q-pt-sm">
        <slot />
      </div>
    </template>
  </q-banner>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue';

export type ExpandableBannerType = 'success' | 'warning' | 'error' | 'info';

const {
  type,
  defaultOpened = true,
  bold = false,
  expandable = true,
} = defineProps<{
  type: ExpandableBannerType;
  title: string;
  defaultOpened?: boolean;
  bold?: boolean;
  expandable?: boolean;
}>();

const slots = useSlots();

const STYLES: Record<ExpandableBannerType, { banner: string; text: string; icon: string }> = {
  success: { banner: 'bg-positive text-white', text: 'text-white', icon: 'check' },
  warning: { banner: 'bg-warning text-black', text: 'text-black', icon: 'warning' },
  error: { banner: 'bg-negative text-white', text: 'text-white', icon: 'error' },
  info: { banner: 'bg-info text-white', text: 'text-white', icon: 'info' },
};

const style = computed(() => STYLES[type]);
const titleClass = computed(() => (bold ? 'text-weight-bold' : ''));
</script>

<style scoped>
.expandable-banner {
  flex-shrink: 0;
}

.expandable-banner :deep(.q-banner__content) {
  min-width: 0;
  overflow-wrap: anywhere;
}

.expandable-banner :deep(.q-hoverable:hover:not(:focus-visible) > .q-focus-helper) {
  opacity: 0;
}

.expandable-banner__description {
  max-height: min(12rem, 25vh);
  padding-bottom: 10px;
  white-space: pre-line;
}

.expandable-banner__description :slotted(ul),
.expandable-banner__description :slotted(ol) {
  margin: 0;
  padding-left: 16px;
}

.expandable-banner__description :slotted(li + li) {
  margin-top: 8px;
}
</style>
