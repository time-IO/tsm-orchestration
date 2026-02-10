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

// Define a type for the processed data entries
interface FormEntry {
  name: string;
  value: number | string | null;
  type: string | null;
}

const formData = ref({
  min_length: null,
  input2: null,
});

const emit = defineEmits(['submit']);

const submitForm = () => {
  const processedData: FormEntry[] = Object.entries(formData.value).map(([key, value]) => {
    let type: FormEntry['type'] = null;

    switch (key) {
      case 'min_length':
        type = 'int';
        break;
      case 'input2':
        type = 'datastream';
        break;
      default:
        break;
    }

    return { name: key, value, type };
  });

  emit('submit', processedData);
  formData.value = { min_length: null, input2: null };
};
</script>

<style scoped></style>
