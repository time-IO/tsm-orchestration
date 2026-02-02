<template>
  <main-layout />
</template>

<script setup lang="ts">
import MainLayout from 'layouts/MainLayout.vue';
import {onMounted} from "vue";
import {useAuthStore} from "stores/authStore";

const authStore = useAuthStore()

onMounted(()=>{
  authStore.initialize()
})

</script>
