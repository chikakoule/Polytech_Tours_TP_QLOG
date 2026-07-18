module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: ['eslint:recommended', 'plugin:vue/vue3-recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  rules: {
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'warn',
  },
  overrides: [
    {
      // Les globales Cypress (cy, describe, it…) n'existent QUE dans les tests
      // E2E : on limite la config Cypress à ces fichiers plutôt que de
      // l'appliquer à tout le frontend.
      files: ['cypress/**/*.js', '**/*.cy.js'],
      extends: ['plugin:cypress/recommended'],
    },
  ],
}
