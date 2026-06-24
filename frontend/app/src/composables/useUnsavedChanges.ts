import { onBeforeUnmount } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';

export function useUnsavedChanges(isDirty: () => boolean) {
  // Browser-Tab schließen / reload
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (isDirty()) {
      e.preventDefault();
    }
  };

  window.addEventListener('beforeunload', handleBeforeUnload);
  onBeforeUnmount(() => window.removeEventListener('beforeunload', handleBeforeUnload));

  // Vue Router Navigation
  onBeforeRouteLeave(() => {
    if (isDirty()) {
      return window.confirm('You have unsaved changes. Are you sure you want to leave?');
    }
  });
}
