import { defineStore } from 'pinia'
import apiClient from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'ADMINISTRATEUR',
    firstName: (state) => state.user?.first_name || state.user?.email || '',
  },
  actions: {
    async login(email, password) {
      const { data } = await apiClient.post('/auth/login', { email, password })
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      // Récupère le prénom depuis le profil pour personnaliser l'accueil.
      try {
        const me = await apiClient.get('/profile/me')
        if (me.data.player) {
          this.user = { ...this.user, first_name: me.data.player.first_name }
          localStorage.setItem('user', JSON.stringify(this.user))
        }
      } catch (e) {
        // profil joueur non obligatoire (ex. admin sans fiche joueur)
      }
      return data
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
