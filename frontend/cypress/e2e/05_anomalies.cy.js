/// <reference types="cypress" />

/**
 * Tests E2E ciblant les anomalies à dominante frontend.
 * Sur l'application SAINE : ces tests PASSENT.
 * Sur la version DÉGRADÉE : ils ÉCHOUENT, prouvant l'anomalie.
 *
 *  - BUG-F5 : le filtre « mes matchs » par défaut (joueur) ne montre que ses matchs.
 *  - BUG-S2 : un nom d'entreprise contenant du HTML est échappé (pas d'exécution XSS).
 */

describe('Anomalies frontend', () => {
  it('BUG-F5 : le filtre « mes matchs » est actif par défaut pour un joueur', () => {
    cy.loginAsPlayer()
    cy.visit('/matches')

    // Le joueur de test (Tech Corp) appartient à une seule équipe : par défaut
    // il ne voit QUE ses matchs. En cochant « Voir tous les matchs », le total
    // doit strictement augmenter (le seed contient des matchs d'autres équipes).
    cy.get('body').then(($body) => {
      const mineCount = $body.find('[data-cy=match-row]').length
      cy.get('[data-cy=show-all]').check()
      cy.wait(500)
      cy.get('[data-cy=match-row]').its('length').should('be.gt', mineCount)
    })
  })

  it("BUG-S2 : un nom d'entreprise malveillant est affiché échappé (pas d'XSS)", () => {
    const xss = `<img src=x onerror="window.__xss=true">`
    const api = Cypress.env('apiUrl')
    const s = Date.now().toString().slice(-6)

    cy.loginAsAdmin().then(() => {
      const headers = { Authorization: `Bearer ${window.localStorage.getItem('token')}` }
      const mkPlayer = (i) =>
        cy.request({
          method: 'POST',
          url: `${api}/players`,
          headers,
          body: {
            first_name: 'Inj',
            last_name: `Ecteur${i}`,
            company: xss,
            license_number: `L9${s}${i}`,
            email: `xss.${s}.${i}@evil.fr`,
          },
        })

      mkPlayer(1).then((r1) =>
        mkPlayer(2).then((r2) =>
          cy.request({
            method: 'POST',
            url: `${api}/teams`,
            headers,
            body: { company: xss, player1_id: r1.body.id, player2_id: r2.body.id },
          }),
        ),
      )
    })

    cy.visit('/admin')
    cy.window().then((win) => {
      win.__xss = false
    })
    cy.get('[data-cy=tab-teams]').click()
    // Le contenu doit apparaître comme TEXTE (échappé), pas exécuté comme HTML.
    cy.get('[data-cy=teams-table]').should('contain', '<img')
    cy.window().its('__xss').should('eq', false)
  })
})
