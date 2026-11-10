<template>
  <help-dialog title="URLs">
    <p class="text-caption">
      Every endpoint is reachable via three URLs. They differ in which data is served and whether a
      login (or other form of authentication) is required.
    </p>

    <q-markup-table flat bordered separator="cell" class="url-help__table">
      <tbody>
        <tr v-for="row in ROWS" :key="row.label">
          <td class="text-weight-bold">{{ row.label }}</td>
          <td>{{ row.description }}</td>
        </tr>
      </tbody>
    </q-markup-table>
  </help-dialog>
</template>

<script setup lang="ts">
import HelpDialog from '@/components/common/HelpDialog.vue';

const ROWS = [
  {
    label: 'Automatic',
    description:
      'Serves the internal data if you are logged in and a member of the project, otherwise the public data. Use it if the same URL should work for everyone.',
  },
  {
    label: 'Public',
    description:
      'Always serves the public data, no login required. A login is ignored, so the result is the same for every user.',
  },
  {
    label: 'Internal',
    description:
      'Always serves the internal data and never falls back to the public data. Requires a login and membership in the permission group of the endpoint, otherwise the request is rejected.',
  },
];
</script>

<style scoped>
.url-help__table td {
  white-space: normal;
  vertical-align: middle;
}
</style>
