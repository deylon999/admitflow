import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import { importX } from 'eslint-plugin-import-x';
import { createTypeScriptImportResolver } from 'eslint-import-resolver-typescript';

export default tseslint.config(
  { ignores: ['dist/**', 'test-results/**', 'playwright-report/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx,mjs,js}'],
    languageOptions: {
      globals: Object.fromEntries(
        [
          'window',
          'document',
          'navigator',
          'localStorage',
          'sessionStorage',
          'location',
          'fetch',
          'Response',
          'Request',
          'Headers',
          'AbortController',
          'AbortSignal',
          'URL',
          'URLSearchParams',
          'TextEncoder',
          'TextDecoder',
          'DOMException',
          'File',
          'Blob',
          'Storage',
          'MutationObserver',
          'HTMLInputElement',
          'HTMLElement',
          'StorageEvent',
          'Event',
          'requestAnimationFrame',
          'setTimeout',
          'clearTimeout',
          'console',
          'process',
          'Buffer',
          'innerWidth',
          'matchMedia',
        ].map((key) => [key, 'readonly']),
      ),
    },
    plugins: { 'import-x': importX },
    settings: {
      'import-x/resolver-next': [createTypeScriptImportResolver({ project: './tsconfig.json' })],
    },
    rules: {
      'no-undef': 'off',
      // Validators intentionally reject control characters in user input.
      'no-control-regex': 'off',
      'no-empty': ['error', { allowEmptyCatch: true }],
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      'import-x/no-cycle': 'error',
      'import-x/no-self-import': 'error',
    },
  },
);
