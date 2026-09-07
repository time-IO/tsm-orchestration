<template>
  <QField ref="qField" v-bind="$attrs">
    <template v-for="(_, slot) of $slots" #[slot]="scope">
      <slot :name="slot" v-bind="scope || {}" />
    </template>
  </QField>
</template>

<script setup lang="ts">
import { QField } from 'quasar';
import { onMounted, ref } from 'vue';

const emit = defineEmits(['click']);
const qField = ref<QField>();

const { disable } = defineProps<{
  disable: boolean;
}>();
onMounted(() => {
  // https://github.com/quasarframework/quasar/issues/8956
  qField.value!.$el.onclick = () => {
    if (!disable) {
      emit('click');
    }
  };
});
</script>
