<script setup>
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
</script>

<template>
  <div class="mx-auto max-w-3xl text-center">
    <div class="mb-8 rounded-2xl bg-gradient-to-br from-padel-600 to-blue-800 px-8 py-16 text-white shadow-lg">
      <div class="text-6xl">🎾</div>
      <h1 class="mt-4 text-4xl font-extrabold">Corpo Padel</h1>
      <p class="mx-auto mt-4 max-w-xl text-lg text-blue-100">
        La plateforme de gestion des tournois de padel inter-entreprises : planning, matchs,
        résultats et classements en un seul endroit.
      </p>

      <div class="mt-8">
        <template v-if="!auth.isAuthenticated">
          <router-link to="/login" class="btn bg-white px-6 py-3 text-padel-600 hover:bg-blue-50" data-cy="home-login">
            Se connecter
          </router-link>
        </template>
        <template v-else>
          <p class="text-xl font-semibold" data-cy="welcome">Bienvenue {{ auth.firstName }} 👋</p>
          <router-link to="/planning" class="mt-4 inline-block btn bg-white px-6 py-3 text-padel-600 hover:bg-blue-50">
            Voir le planning
          </router-link>
        </template>
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-3">
      <div class="card text-left">
        <div class="text-2xl">📅</div>
        <h3 class="mt-2 font-semibold">Planning</h3>
        <p class="mt-1 text-sm text-gray-600">Tous les événements de la saison dans un calendrier.</p>
      </div>
      <div class="card text-left">
        <div class="text-2xl">⚽</div>
        <h3 class="mt-2 font-semibold">Matchs</h3>
        <p class="mt-1 text-sm text-gray-600">Vos prochains matchs et ceux de toutes les équipes.</p>
      </div>
      <div class="card text-left">
        <div class="text-2xl">📊</div>
        <h3 class="mt-2 font-semibold">Classement</h3>
        <p class="mt-1 text-sm text-gray-600">Le classement général des entreprises en temps réel.</p>
      </div>
    </div>
  </div>
</template>
