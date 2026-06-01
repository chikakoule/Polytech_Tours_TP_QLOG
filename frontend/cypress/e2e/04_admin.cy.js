/// <reference types="cypress" />

describe('Parcours administrateur (gestion)', () => {
  beforeEach(() => {
    cy.loginAsAdmin()
  })

  it("affiche la page d'administration avec ses onglets", () => {
    cy.visit('/admin')
    cy.contains('h1', 'Administration')
    cy.get('[data-cy=tab-players]').should('exist')
    cy.get('[data-cy=tab-teams]').should('exist')
    cy.get('[data-cy=tab-pools]').should('exist')
    cy.get('[data-cy=tab-accounts]').should('exist')
  })

  it('crée un joueur via le formulaire admin', () => {
    const suffix = Date.now().toString().slice(-6)
    cy.visit('/admin')
    cy.get('[data-cy=p-first]').type('Testeur')
    cy.get('[data-cy=p-last]').type('Cypress')
    cy.get('[data-cy=p-company]').type('QA Corp')
    cy.get('[data-cy=p-license]').type(`L${suffix}`)
    cy.get('[data-cy=p-email]').type(`testeur.${suffix}@qa.fr`)
    cy.get('[data-cy=p-submit]').click()
    cy.get('[data-cy=players-table]').should('contain', 'Testeur')
  })

  it('refuse un numéro de licence invalide (validation serveur)', () => {
    cy.visit('/admin')
    cy.get('[data-cy=p-first]').type('Mauvais')
    cy.get('[data-cy=p-last]').type('Licence')
    cy.get('[data-cy=p-company]').type('QA Corp')
    cy.get('[data-cy=p-license]').type('INVALIDE')
    cy.get('[data-cy=p-email]').type(`bad.${Date.now()}@qa.fr`)
    cy.get('[data-cy=p-submit]').click()
    cy.get('[data-cy=admin-error]').should('be.visible')
  })
})
