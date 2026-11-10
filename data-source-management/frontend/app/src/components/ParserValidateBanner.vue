<template>
  <expandable-banner
    v-if="!parsingResult.is_valid"
    type="error"
    bold
    title="Parsing failed"
    class="q-mt-lg"
    :class="{ 'validation-table--stale': haveSettingsChanged }"
  >
    {{ parsingResult.error }}
  </expandable-banner>
  <expandable-banner
    v-else-if="parsingResult.is_valid && parsingResult.warnings.length > 0"
    type="warning"
    bold
    :title="`Parsing finished with ${parsingResult.warnings.length} ${
      parsingResult.warnings.length === 1 ? 'warning' : 'warnings'
    }`"
    class="q-mt-lg"
    :class="{ 'validation-table--stale': haveSettingsChanged }"
  >
    <ul>
      <li v-for="(warning, index) in parsingResult.warnings" :key="index">{{ warning }}</li>
    </ul>
  </expandable-banner>
  <expandable-banner
    v-else-if="parsingResult.is_valid && parsingResult.data.length > 0"
    type="success"
    title="Parsing succeeded"
    class="q-mt-lg"
    :class="{ 'validation-table--stale': haveSettingsChanged }"
  />
</template>

<script setup lang="ts">
import ExpandableBanner from '@/components/common/ExpandableBanner.vue';
import type { ParsingResult } from '@/services/types';

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
