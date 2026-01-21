<template>
  <q-form @submit.prevent="submitForm">
    <q-card>
      <q-card-section>
        <h5>Function A Form</h5>
      </q-card-section>

      <q-card-section>
        <q-input v-model="formData.min_length" label="min_length" required type="number" />

        <q-input v-model="formData.input2" label="Input 2" required type="number" />
      </q-card-section>

      <q-card-actions align="right">
        <q-btn color="grey" label="Add" type="submit" />
        <q-space></q-space>
      </q-card-actions>
    </q-card>
  </q-form>
</template>

<script lang="ts" setup>
import { ref } from 'vue';

const formData = ref({
  min_length: null,
  input2: null,
});

const emit = defineEmits(['submit']);

const submitForm = () => {
  const processedData = Object.entries(formData.value).map(([key, value]) => {
    // Map value types to appropriate Vue type descriptors
    let valueWithType = {name: key , value: value};
    switch (key) {
      case 'min_length':
      {
        valueWithType.type = 'int';
      }
        break;
      case 'input2':{
        valueWithType.type = 'datastream';
      }
        break;
      default:
        break;
    }
    return valueWithType;
  })

  emit('submit', processedData);
  formData.value = { input1: '', input2: null }; // Reset form
};
</script>

<style scoped></style>
