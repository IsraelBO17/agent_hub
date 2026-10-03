// @ts-check
// Lint is how the standard's structure is enforced (standard §23). `eslint . --max-warnings 0`.
import { fixupPluginRules } from '@eslint/compat'
import js from '@eslint/js'
import boundaries from 'eslint-plugin-boundaries'
import checkFile from 'eslint-plugin-check-file'
import { createTypeScriptImportResolver } from 'eslint-import-resolver-typescript'
import { importX } from 'eslint-plugin-import-x'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'
import { builtinRules } from 'eslint/use-at-your-own-risk'
import globals from 'globals'
import tseslint from 'typescript-eslint'

// A later block REPLACES a rule's options, so shared import patterns are constants each block re-lists.
const parentBan = { group: ['../*', '../**', './../*'], message: 'No parent-relative imports. Use the @/ alias.' }
const deepModuleBan = { group: ['@/modules/*/*', '@/modules/*/**'], message: "Import a module through its index: '@/modules/<name>'." }
const iconBan = { name: 'lucide-react', message: 'Import icons from @/components/ui/icon.' }

// Files `npx shadcn add` wrote. They stay close to upstream, so they skip the stylistic rules below.
// Add each new one here (recipe 4). App composites in components/ui are not listed: they're held to every rule.
const vendored = [
  'src/components/ui/{alert-dialog,button,card,dialog,field,input,label,separator,sheet,sidebar,skeleton,textarea,tooltip}.tsx',
  'src/hooks/use-mobile.ts',
]

// The standard's §7 import table. Elements are matched in order; the first match wins.
const elements = [
  { type: 'app', pattern: 'src/app', partialMatch: false },
  { type: 'module', pattern: 'src/modules/*', capture: ['name'], partialMatch: false },
  { type: 'components', pattern: 'src/components', partialMatch: false },
  { type: 'generated', pattern: 'src/service/generated', partialMatch: false },
  { type: 'service', pattern: 'src/service', partialMatch: false },
  { type: 'models', pattern: 'src/models', partialMatch: false },
  { type: 'store', pattern: 'src/store', partialMatch: false },
  { type: 'provider', pattern: 'src/provider', partialMatch: false },
  { type: 'lib', pattern: 'src/lib', partialMatch: false },
  { type: 'utils', pattern: 'src/utils', partialMatch: false },
  { type: 'hooks', pattern: 'src/hooks', partialMatch: false },
  { type: 'mocks', pattern: 'src/mocks', partialMatch: false },
  { type: 'styles', pattern: 'src/styles', partialMatch: false },
  { type: 'main', pattern: 'src', partialMatch: false }, // what's left: main.tsx
]
/** @type {Record<string, string[]>} */
const mayImport = {
  main: ['app', 'provider', 'lib', 'mocks', 'styles'],
  app: ['module', 'provider', 'components', 'lib'],
  provider: ['module', 'service', 'generated', 'store', 'components', 'lib', 'utils'],
  module: ['module', 'components', 'service', 'generated', 'models', 'store', 'hooks', 'utils', 'lib'],
  components: ['components', 'hooks', 'utils', 'lib'],
  service: ['service', 'generated', 'models', 'lib', 'utils'],
  generated: [],
  models: ['models', 'generated', 'utils'],
  store: ['store', 'models', 'utils', 'lib'],
  hooks: ['hooks', 'utils', 'lib'],
  lib: ['lib', 'utils'],
  utils: ['utils'],
  mocks: ['mocks', 'models', 'generated', 'utils'],
}
const layerPolicies = Object.entries(mayImport).map(([from, to]) => ({
  from: { element: { type: from } },
  allow: { to: { element: { types: { anyOf: to } } } },
}))

export default defineConfig([
  globalIgnores(['dist', 'coverage', 'node_modules', 'playwright-report', 'test-results', 'artifacts', 'src/service/generated', '.vitest']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, tseslint.configs.strictTypeChecked, tseslint.configs.stylisticTypeChecked],
    languageOptions: {
      ecmaVersion: 2023,
      globals: globals.browser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/ban-ts-comment': ['error', {
        'ts-expect-error': 'allow-with-description', 'ts-ignore': true, 'ts-nocheck': true, 'ts-check': false, minimumDescriptionLength: 10,
      }],
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/prefer-nullish-coalescing': ['error', { ignorePrimitives: { string: true } }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', destructuredArrayIgnorePattern: '^_' }],
      'no-console': 'error',
      'max-lines': ['warn', { max: 250, skipBlankLines: true, skipComments: true }],
      'no-restricted-imports': ['error', { paths: [iconBan], patterns: [parentBan, deepModuleBan] }],
    },
  },
  // One rule id has one severity, so the 400-line hard cap re-registers core max-lines under a second name.
  {
    files: ['**/*.{ts,tsx}'],
    plugins: { local: { rules: { 'max-lines': /** @type {never} */ (builtinRules.get('max-lines')) } } },
    rules: { 'local/max-lines': ['error', { max: 400, skipBlankLines: true, skipComments: true }] },
  },
  {
    files: ['src/**/*.{ts,tsx}'],
    extends: [reactHooks.configs.flat.recommended, reactRefresh.configs.vite, jsxA11y.flatConfigs.strict],
    // eslint-plugin-react 7.37 doesn't declare ESLint 10 yet; fixupPluginRules shims the APIs it lost.
    plugins: { react: fixupPluginRules(react) },
    languageOptions: { parserOptions: { ecmaFeatures: { jsx: true } } },
    settings: { react: { version: '19.3' } },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...react.configs.flat['jsx-runtime'].rules,
      'react/no-multi-comp': ['error', { ignoreStateless: false }],
      'react/prop-types': 'off',
    },
  },
  {
    files: ['src/**/*.{ts,tsx}', 'scripts/**/*.ts', 'e2e/**/*.ts'],
    plugins: { 'check-file': checkFile },
    rules: {
      'check-file/filename-naming-convention': ['error', { '**/*.{ts,tsx}': 'KEBAB_CASE' }, { ignoreMiddleExtensions: true }],
      'check-file/folder-naming-convention': ['error', { 'src/**/': 'KEBAB_CASE', 'scripts/**/': 'KEBAB_CASE' }],
    },
  },
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { boundaries },
    settings: {
      'import/resolver': { typescript: { project: './tsconfig.app.json' } },
      'boundaries/elements': elements,
    },
    rules: {
      'boundaries/dependencies': ['error', {
        default: 'disallow',
        policies: [
          ...layerPolicies,
          // Outside a module, import it only through its index.ts …
          { from: { element: { type: '!module' } }, disallow: { to: { element: { type: 'module', fileInternalPath: '!index.ts' } } } },
          // … and a module never imports another module, except the auth module's index.
          { from: { element: { type: 'module' } }, disallow: { to: { element: {
            type: 'module', captured: { name: '!{{ from.element.captured.name }}' },
          } } } },
          { from: { element: { type: 'module' } }, allow: { to: { element: { type: 'module', captured: { name: 'auth' }, fileInternalPath: 'index.ts' } } } },
        ],
      }],
    },
  },
  // Inside a module its own deep imports are fine (boundaries polices the others).
  { files: ['src/modules/**/*.{ts,tsx}'], rules: { 'no-restricted-imports': ['error', { paths: [iconBan], patterns: [parentBan] }] } },
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { 'import-x': importX },
    settings: { 'import-x/resolver-next': [createTypeScriptImportResolver({ project: './tsconfig.app.json' })] },
    rules: { 'import-x/no-cycle': 'error', 'import-x/no-duplicates': 'error' },
  },
  // Vendored shadcn primitives keep their upstream shape (standard §7, §23); app composites beside them don't.
  {
    files: ['src/components/ui/**/*.tsx'],
    rules: {
      'no-restricted-imports': ['error', { patterns: [parentBan, deepModuleBan] }],
      'react-refresh/only-export-components': 'off',
    },
  },
  {
    files: vendored,
    extends: [tseslint.configs.disableTypeChecked],
    rules: {
      'react/no-multi-comp': 'off',
      'max-lines': 'off',
      'local/max-lines': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'jsx-a11y/label-has-associated-control': 'off',
      '@typescript-eslint/consistent-type-definitions': 'off',
      '@typescript-eslint/array-type': 'off',
    },
  },
  { files: ['src/models/**', 'src/mocks/**', 'src/styles/**'], rules: { 'max-lines': 'off' } },
  // Tests reach into the layer they test and into mocks/ and test/.
  { files: ['src/**/*.test.{ts,tsx}', 'src/test/**'], rules: { 'boundaries/dependencies': 'off', 'react/no-multi-comp': 'off' } },
  { files: ['*.{js,ts}', 'scripts/**/*.ts', 'e2e/**/*.ts'], languageOptions: { globals: globals.node } },
  { files: ['**/*.js'], extends: [tseslint.configs.disableTypeChecked] },
])
