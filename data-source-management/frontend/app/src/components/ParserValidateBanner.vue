<template>
  <expandable-banner
    v-if="!parsingResult.is_valid"
    type="error"
    bold
    title="Parsing failed"
    class="q-mt-lg"
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
  />
</template>

<script setup lang="ts">
import ExpandableBanner from '@/components/common/ExpandableBanner.vue';
import type { ParsingResult } from '@/services/types';

defineProps<{
  parsingResult: ParsingResult;
}>();
</script>
