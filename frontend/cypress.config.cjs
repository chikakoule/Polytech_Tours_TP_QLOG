// Config en CommonJS (.cjs) : le projet est en "type":"module", or Cypress
// charge sa config via un bundling qui échoue sur une config ESM dans ce cas.
// Le .cjs est explicitement interprété en CommonJS et fonctionne sur tous les OS.
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5173',
    specPattern: 'cypress/e2e/**/*.cy.js',
    supportFile: 'cypress/support/e2e.js',
    fixturesFolder: 'cypress/fixtures',
    video: false,
    defaultCommandTimeout: 8000,
    env: {
      apiUrl: 'http://localhost:8000/api/v1',
      adminEmail: 'admin@padel.com',
      adminPassword: 'Admin@2025!',
      playerEmail: 'joueur@padel.com',
      playerPassword: 'Joueur@2025!',
    },
  },
})
