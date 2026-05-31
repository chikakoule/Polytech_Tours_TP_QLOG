<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <nav class="border-b border-gray-200 bg-white">
    <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
      <router-link to="/" class="flex items-center gap-2 text-lg font-bold text-padel-600">
        <span>🎾</span> Corpo Padel
      </router-link>

      <div v-if="auth.isAuthenticated" class="flex items-center gap-1 text-sm">
        <router-link class="rounded px-3 py-1.5 hover:bg-gray-100" to="/planning">Planning</router-link>
        <router-link class="rounded px-3 py-1.5 hover:bg-gray-100" to="/matches">Matchs</router-link>
        <router-link class="rounded px-3 py-1.5 hover:bg-gray-100" to="/results">Résultats</router-link>
        <router-link class="rounded px-3 py-1.5 hover:bg-gray-100" to="/profile">Profil</router-link>
        <router-link
          v-if="auth.isAdmin"
          class="rounded px-3 py-1.5 font-medium text-padel-600 hover:bg-padel-50"
          to="/admin"
          data-cy="nav-admin"
          >Administration</router-link
        >
        <button class="ml-2 btn-secondary" data-cy="logout" @click="logout">Déconnexion</button>
      </div>

      <div v-else>
        <router-link to="/login" class="btn-primary" data-cy="nav-login">Se connecter</router-link>
      </div>
    </div>
  </nav>
</template>
