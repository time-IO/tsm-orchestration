<template>
  <div class="row items-stretch q-col-gutter-md">
    <div class="col">
      <q-file
        :model-value="file"
        filled
        :label="`${allowedFileTypeName} file`"
        :accept="allowedFileType"
        clearable
        :disable="isValidating"
        @update:model-value="handleFileChange"
        :max-file-size="1024 * 1024 * 10"
        :max-files="1"
        @rejected="wasFileRejected = true"
        :error="wasFileRejected"
        error-message="File type is invalid or file is too large"
        hint="Maximum allowed size is 10 MB."
      >
        <template #prepend>
          <q-icon name="upload_file" />
        </template>
      </q-file>
    </div>
    <div class="col-auto">
      <q-btn
        class="full-height"
        unelevated
        color="primary"
        :label="isAlreadyValidated ? 'Validated' : 'Validate'"
        :loading="isValidating"
        :disable="!file || isAlreadyValidated"
        @click="$emit('validate')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const file = defineModel<File | null>('file', { default: null });
const wasFileRejected = defineModel<boolean>('wasFileRejected', { default: false });

defineProps<{
  isValidating: boolean;
  isAlreadyValidated: boolean;
  allowedFileType: string;
  allowedFileTypeName: string;
}>();

const emit = defineEmits<{
  change: [file: File | null];
  validate: [];
}>();

function handleFileChange(newFile: File | null) {
  wasFileRejected.value = false;
  file.value = newFile;
  emit('change', newFile);
}
</script>
