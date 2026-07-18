<script setup>
import { onMounted, ref } from 'vue'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const myResults = ref(null)
const rankings = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const ranks = await apiClient.get('/results/rankings')
    rankings.value = ranks.data.rankings
    if (!auth.isAdmin) {
      try {
        const mine = await apiClient.get('/results/my-results')
        myResults.value = mine.data
      } catch (e) {
        myResults.value = null
      }
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">Résultats</h1>

    <section v-if="myResults" class="mb-10">
      <h2 class="mb-3 text-lg font-semibold">Mes résultats</h2>
      <div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="card text-center">
          <p class="text-2xl font-bold">{{ myResults.statistics.total_matches }}</p>
          <p class="text-xs text-gray-500">Matchs joués</p>
        </div>
        <div class="card text-center">
          <p class="text-2xl font-bold text-green-600">{{ myResults.statistics.wins }}</p>
          <p class="text-xs text-gray-500">Victoires</p>
        </div>
        <div class="card text-center">
          <p class="text-2xl font-bold text-red-600">{{ myResults.statistics.losses }}</p>
          <p class="text-xs text-gray-500">Défaites</p>
        </div>
        <div class="card text-center">
          <p class="text-2xl font-bold">{{ myResults.statistics.win_rate }}%</p>
          <p class="text-xs text-gray-500">Taux de victoire</p>
        </div>
      </div>

      <p v-if="myResults.results.length === 0" class="text-sm text-gray-500">
        Aucun match terminé pour l'instant.
      </p>
      <div v-else class="space-y-2">
        <div v-for="r in myResults.results" :key="r.match_id" class="card flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">
              <span data-cy="result-date">{{ r.date }}</span> · Piste {{ r.court_number }}
            </p>
            <p class="font-medium">vs {{ r.opponents.company }}</p>
            <p class="text-sm text-gray-600">{{ r.opponents.players.join(' & ') }}</p>
          </div>
          <div class="text-right">
            <span
              class="badge"
              :class="r.result === 'VICTOIRE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
              >{{ r.result }}</span
            >
            <p class="mt-1 text-sm font-medium">{{ r.score }}</p>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold">Classement général</h2>
      <div class="overflow-x-auto rounded-lg border border-gray-200">
        <table class="w-full text-sm" data-cy="rankings-table">
          <thead class="bg-padel-600 text-white">
            <tr>
              <th class="px-4 py-2 text-left">#</th>
              <th class="px-4 py-2 text-left">Entreprise</th>
              <th class="px-4 py-2 text-center">Joués</th>
              <th class="px-4 py-2 text-center">V</th>
              <th class="px-4 py-2 text-center">D</th>
              <th class="px-4 py-2 text-center">Sets +/-</th>
              <th class="px-4 py-2 text-center">Points</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rankings" :key="row.company" class="border-t border-gray-100">
              <td class="px-4 py-2 font-semibold">{{ row.position }}</td>
              <td class="px-4 py-2">{{ row.company }}</td>
              <td class="px-4 py-2 text-center">{{ row.matches_played }}</td>
              <td class="px-4 py-2 text-center">{{ row.wins }}</td>
              <td class="px-4 py-2 text-center">{{ row.losses }}</td>
              <td class="px-4 py-2 text-center">{{ row.sets_won }}/{{ row.sets_lost }}</td>
              <td class="px-4 py-2 text-center font-bold text-padel-600">{{ row.points }}</td>
            </tr>
            <tr v-if="rankings.length === 0">
              <td colspan="7" class="px-4 py-4 text-center text-gray-500">Aucun résultat pour le moment.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
