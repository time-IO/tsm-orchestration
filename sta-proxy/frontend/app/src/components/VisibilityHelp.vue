<template>
  <help-dialog title="Access">
    <p class="text-caption">
      Every STA endpoint serves a public and an internal access. data of its project, internal
      endpoints additionally serve the data that is restricted to the members of the project.
    </p>

    <q-markup-table flat bordered separator="cell" class="visibility-help__table">
      <tbody>
        <tr v-for="row in ROWS" :key="row.visibility">
          <td class="visibility-help__badge">
            <visibility-badge :visibility="row.visibility" class="full-width justify-center" />
          </td>
          <td>{{ row.description }}</td>
        </tr>
      </tbody>
    </q-markup-table>

    <p class="text-caption q-mt-md q-mb-none">
      Whether data is public or internal follows the visibility settings of the related entities in
      the Sensor Management System (SMS), such as configurations and their devices.
    </p>
  </help-dialog>
</template>

<script setup lang="ts">
import HelpDialog from '@/components/common/HelpDialog.vue';
import VisibilityBadge from '@/components/common/VisibilityBadge.vue';
import type { VisibilityName } from '@/utils/visibility';

const ROWS: { visibility: VisibilityName; description: string }[] = [
  {
    visibility: 'public',
    description:
      'The public access is available to everyone and requires no login. It is limited to publicly available data.',
  },
  {
    visibility: 'internal',
    description:
      'The internal access is limited to members of the respective project (permission group) and requires a login or another form of authentication.',
  },
];
</script>

<style scoped>
.visibility-help__table td {
  white-space: normal;
  vertical-align: middle;
}

.visibility-help__badge {
  width: 110px;
}
</style>
