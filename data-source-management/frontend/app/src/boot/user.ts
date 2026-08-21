import { defineBoot } from '#q-app/wrappers';
import { useAuthStore } from 'stores/authStore';

export default defineBoot(async () => {
  const authStore = useAuthStore();

  if (authStore.isAuthenticated) {
    await authStore.fetchUserInfo();
  }
});
