<template>
  <q-form @submit.prevent="submitForm">
    <q-card>
      <q-card-section>
        <h5>Function A Form 2</h5>
      </q-card-section>

      <q-card-section>
        <q-input
          v-model="formData.input1"
          label="Input 1"
          type="text"
          required
        />

        <q-input
          v-model="formData.input2"
          label="Input 2"
          type="number"
          required
        />
      </q-card-section>

      <q-card-actions align="right">
        <q-btn label="Add" type="submit" color="primary" />
      </q-card-actions>
    </q-card>
  </q-form>
</template>

<script setup lang="ts">

import { ref } from 'vue';

const formData = ref({
  input1: '',
  input2: null
});

const emit = defineEmits(['submit']);

const submitForm = () => {
  emit('submit', formData.value);
  formData.value = { input1: '', input2: null }; // Reset form
};

</script>

<style scoped></style>
