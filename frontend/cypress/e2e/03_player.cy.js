/// <reference types="cypress" />

describe('Parcours joueur (consultation)', () => {
  beforeEach(() => {
    cy.loginAsPlayer()
  })

  it('le joueur navigue dans les pages autorisées', () => {
    cy.visit('/results')
    cy.contains('Classement général')
    cy.get('[data-cy=rankings-table] tbody tr').its('length').should('be.gte', 1)

    cy.visit('/planning')
    cy.get('[data-cy=month-label]').should('be.visible')
  })

  it("le joueur n'a pas accès à l'administration", () => {
    cy.visit('/admin')
    cy.location('pathname').should('eq', '/')
  })

  it('le joueur voit ses statistiques personnelles', () => {
    cy.visit('/results')
    cy.contains('Mes résultats')
  })
})
