import { quasarViteTestingConfig } from '@quasar/quasar-app-extension-testing-unit-vitest/config';
import { defineConfig, mergeConfig } from 'vitest/config';

export default defineConfig(async () =>
  mergeConfig(await quasarViteTestingConfig(), {
    test: {
      environment: 'happy-dom',
      setupFiles: 'test/setup-file.ts',
      include: ['test/components/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    },
  }),
);
