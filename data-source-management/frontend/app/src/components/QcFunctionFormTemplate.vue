<template>
  <q-form @submit.prevent="submitForm">
    <q-card>
      <q-card-section>
        <q-item>
          <q-item-section class="text-h5">
            <div class="row items-center no-wrap">
              <span>{{ functionTitle }}</span>
              <saqc-info-icon color="grey" class="q-ml-sm" :label="functionTitle" />
            </div>
          </q-item-section>

          <q-item-section side>
            <q-icon name="close" class="cursor-pointer" @click="removeForm" />
          </q-item-section>
        </q-item>
      </q-card-section>

      <q-card-section>
        <q-input
          filled
          v-model="label"
          label="Label (optional)"
          hint="A specific name to help you find this function later"
        />
      </q-card-section>

      <q-card-section>
        <slot></slot>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn color="green" label="Add" type="submit" />
      </q-card-actions>
    </q-card>
  </q-form>
</template>

<script setup lang="ts">
import SaqcInfoIcon from 'components/SaqcInfoIcon.vue';

defineProps<{
  functionTitle: string;
}>();

const label = defineModel<string | undefined>('label');

const emit = defineEmits(['submit', 'remove']);

const submitForm = () => {
  emit('submit');
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
