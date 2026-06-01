/// <reference types="cypress" />

/**
 * Test d'exemple — point de départ pour vos tests End-to-End.
 *
 * Pré-requis : le backend (http://localhost:8000) et le frontend
 * (http://localhost:5173) doivent tourner. Lancez :
 *   npx cypress open   # mode interactif
 *   npx cypress run    # mode headless (CI)
 *
 * À vous d'écrire les parcours visiteur / joueur / administrateur, et les
 * tests qui prouvent les anomalies détectées en recette.
 */

describe('Exemple', () => {
  it("charge la page d'accueil", () => {
    cy.visit('/')
    cy.contains('Corpo Padel')
  })
})
