/// <reference types="cypress" />

describe('Parcours visiteur (non authentifié)', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  it("affiche l'accueil avec le bouton de connexion", () => {
    cy.visit('/')
    cy.contains('Corpo Padel')
    cy.get('[data-cy=home-login]').should('be.visible')
  })

  it("redirige vers /login quand on tente d'accéder à une page protégée", () => {
    cy.visit('/planning')
    cy.location('pathname').should('eq', '/login')
  })

  it("redirige l'accès admin d'un visiteur vers /login", () => {
    cy.visit('/admin')
    cy.location('pathname').should('eq', '/login')
  })
})
