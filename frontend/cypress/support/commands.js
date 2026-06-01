// Commandes personnalisées réutilisables.

/**
 * Connexion via l'API : pose le token dans localStorage (login rapide pour les
 * tests qui ne testent pas l'IHM de login elle-même).
 */
Cypress.Commands.add('loginAs', (email, password) => {
  cy.request('POST', `${Cypress.env('apiUrl')}/auth/login`, { email, password }).then((resp) => {
    expect(resp.status).to.eq(200)
    window.localStorage.setItem('token', resp.body.access_token)
    window.localStorage.setItem('user', JSON.stringify(resp.body.user))
  })
})

Cypress.Commands.add('loginAsAdmin', () => {
  cy.loginAs(Cypress.env('adminEmail'), Cypress.env('adminPassword'))
})

Cypress.Commands.add('loginAsPlayer', () => {
  cy.loginAs(Cypress.env('playerEmail'), Cypress.env('playerPassword'))
})

/** Connexion via l'IHM (pour tester le formulaire lui-même). */
Cypress.Commands.add('loginViaUi', (email, password) => {
  cy.visit('/login')
  cy.get('[data-cy=email]').clear().type(email)
  cy.get('[data-cy=password]').clear().type(password, { log: false })
  cy.get('[data-cy=submit]').click()
})
