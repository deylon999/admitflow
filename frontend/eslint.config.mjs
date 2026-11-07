import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  ...tseslint.configs.recommended.map(config => ({ ...config, files: ['src/**/*.{ts,tsx}', 'tests/**/*.ts', '*.ts'] })),
  {
    files: ['src/**/*.{ts,tsx}', 'tests/**/*.ts', '*.ts'],
    rules: {
      ...eslint.configs.recommended.rules,
      // TypeScript checks globals and unused symbols with the project's DOM lib.
      'no-undef': 'off',
      'no-unused-vars': 'off',
    },
  },
  {
    files: ['scripts/*.mjs', '*.mjs'],
    languageOptions: { globals: {
      process: 'readonly', console: 'readonly', Buffer: 'readonly',
      setTimeout: 'readonly', clearTimeout: 'readonly', fetch: 'readonly', URL: 'readonly',
    } },
    rules: eslint.configs.recommended.rules,
  },
];
