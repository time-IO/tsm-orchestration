<template>
  <span class="external-link-text">
    <span :class="{ 'text-weight-bold': boldText }">
      <slot>{{ text }}</slot>
    </span>
    <open-in-new-tab-button
      v-if="!hideButton"
      dense
      size="xs"
      color="grey-7"
      class="q-ml-xs"
      :href="href"
      :tooltip="tooltip"
    />
  </span>
</template>

<script setup lang="ts">
import OpenInNewTabButton from '@/components/common/OpenInNewTabButton.vue';

const {
  href,
  text = '',
  tooltip = 'Open in new tab',
  boldText = true,
  hideButton = false,
} = defineProps<{
  href: string;
  text?: string;
  tooltip?: string;
  boldText?: boolean;
  hideButton?: boolean;
}>();
</script>

<style scoped>
.external-link-text {
  font: inherit;
  color: inherit;
  letter-spacing: inherit;
}
</style>
