<template>
  <q-drawer
    v-model="open"
    side="right"
    show-if-above
    bordered
    :width="drawerWidth"
    :breakpoint="breakpoint"
  >
    <slot />
  </q-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';

const props = withDefaults(
  defineProps<{
    width?: number; // below this width the drawer is an overlay and not opened initially
    breakpoint?: number;
  }>(),
  {
    width: 500,
    breakpoint: 1024,
  },
);

const open = defineModel<boolean>({ default: false });

const $q = useQuasar();

const drawerWidth = computed(() => Math.min(props.width, $q.screen.width - 20));
</script>
