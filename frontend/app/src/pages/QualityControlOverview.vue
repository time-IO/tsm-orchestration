<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Quality Control Settings</h5>
    <div class="row q-mb-lg">
      <q-space/>
      <q-btn color="green" :label="t('newSetting')" to="/quality-control/new"/>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n()
</script>

<style scoped>

</style>
