<template>
  <QField :ref="Q_FIELD_REF_NAME" v-bind="$attrs">
    <template v-for="(_, slot) of $slots" #[slot]="scope">
      <slot :name="slot" v-bind="scope || {}" />
    </template>
  </QField>
</template>

<script setup lang="ts">
import { QField } from 'quasar';
import { onMounted, useTemplateRef } from 'vue';

const { disable } = defineProps<{
  disable: boolean;
}>();

const emit = defineEmits(['click']);
const Q_FIELD_REF_NAME = 'qField';
const qField = useTemplateRef<QField>(Q_FIELD_REF_NAME);

onMounted(() => {
  // https://github.com/quasarframework/quasar/issues/8956
  qField.value!.$el.onclick = () => {
    if (!disable) {
      emit('click');
    }
  };
});
</script>
