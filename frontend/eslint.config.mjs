import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  { ignores: ['dist/**', 'node_modules/**', 'preview/**'] },
  ...tseslint.configs.recommended.map(config => ({ ...config, files: ['src/**/*.{ts,tsx}'] })),
  {
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      ...eslint.configs.recommended.rules,
      // TypeScript checks globals and unused symbols with the project's DOM lib.
      'no-undef': 'off',
      'no-unused-vars': 'off',
    },
  },
];
