/// <reference types="cypress" />

describe('Authentification', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  it('connexion réussie en tant administrateur', () => {
    cy.loginViaUi(Cypress.env('adminEmail'), Cypress.env('adminPassword'))
    cy.location('pathname').should('eq', '/')
    cy.get('[data-cy=nav-admin]').should('exist')
  })

  it('connexion échouée affiche un message générique', () => {
    cy.loginViaUi(Cypress.env('adminEmail'), 'mauvaisMotDePasse')
    cy.get('[data-cy=login-error]').should('be.visible')
    cy.get('[data-cy=attempts]').should('contain', 'Tentatives restantes')
  })

  it('déconnexion ramène à la page de login', () => {
    cy.loginAsAdmin()
    cy.visit('/')
    cy.get('[data-cy=logout]').click()
    cy.location('pathname').should('eq', '/login')
  })
})
