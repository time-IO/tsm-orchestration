<template>
 <q-page class="flex flex-center">
    <div class="q-pa-md text-center">
      <q-spinner-dots color="primary" size="40px" />
      <p>Processing authentication...</p>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import {useAuthStore} from "stores/authStore";

const authStore = useAuthStore()

onMounted(async () => {
    try {
    await authStore.handleCallback()
    // await authStore.navigateAfterLogin()
  } catch (error) {
    console.error('Authentication failed:', error)
  }

})
</script>

<style scoped>

</style>
