<template>
  <q-banner
    v-if="!parsingResult.is_valid"
    class="bg-negative text-white q-mt-lg"
    :class="{ 'validation-table--stale': haveSettingsChanged }"
  >
    <template #avatar>
      <q-icon name="error" />
    </template>
    Parsing failed: {{ parsingResult.error }}
  </q-banner>
  <q-banner
    v-if="parsingResult.is_valid && parsingResult.warnings.length > 0"
    class="bg-warning text-black q-mt-lg"
    :class="{ 'validation-table--stale': haveSettingsChanged }"
  >
    <template #avatar>
      <q-icon name="warning" />
    </template>
    <div class="text-weight-bold q-mt-sm">Parsing finished with warnings</div>
    <ul>
      <li v-for="(warning, index) in parsingResult.warnings" :key="index" class="q-mt-sm">
        {{ warning }}
      </li>
    </ul>
  </q-banner>
  <q-banner
    v-if="parsingResult.is_valid && parsingResult.data.length"
    class="bg-positive text-white q-mt-lg"
    :class="{ 'validation-table--stale': haveSettingsChanged }"
  >
    <template #avatar>
      <q-icon name="check_circle" />
    </template>
    Parsing succeeded.
  </q-banner>
</template>

<script setup lang="ts">
import type { ParsingResult } from 'src/services/types';

defineProps<{
  parsingResult: ParsingResult;
  haveSettingsChanged: boolean;
}>();
</script>

<style scoped>
.validation-table--stale {
  opacity: 0.4;
}
</style>
