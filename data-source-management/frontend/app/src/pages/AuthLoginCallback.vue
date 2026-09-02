<template>
  <q-page class="flex flex-center">
    <div class="q-pa-md text-center">
      <q-spinner-dots color="primary" size="40px" />
      <p>Processing authentication...</p>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'stores/authStore';

const authStore = useAuthStore();
const router = useRouter();

onMounted(async () => {
  try {
    await authStore.handleLoginCallback();
    await router.push('/');
  } catch (error) {
    console.error('Authentication failed:', error);
  }
});
</script>

<style scoped></style>
