<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const matches = ref([])
const loading = ref(true)

// Joueur : par défaut on ne montre QUE ses matchs (filtre actif).
// Admin : par défaut tous les matchs.
const showAll = ref(auth.isAdmin)
const statusFilter = ref('')

const dateFmt = new Intl.DateTimeFormat('fr-FR', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

function formatDateTime(ev) {
  const d = new Date(`${ev.date}T${ev.time}:00`)
  return `${dateFmt.format(d)} à ${ev.time}`
}

async function load() {
  loading.value = true
  const params = {}
  // BUG-F5 (sain) : pour un joueur sans "voir tout", on transmet my_matches=true.
  if (!auth.isAdmin && !showAll.value) {
    params.my_matches = true
  }
  if (statusFilter.value) {
    params.status = statusFilter.value
  }
  try {
    const { data } = await apiClient.get('/matches', { params })
    matches.value = data.matches
  } finally {
    loading.value = false
  }
}

const playersOf = (team) => team.players.map((p) => `${p.first_name} ${p.last_name}`).join(' & ')

const statusBadge = (status) => {
  if (status === 'A_VENIR') return { label: 'À venir', cls: 'bg-blue-100 text-blue-700' }
  if (status === 'ANNULE') return { label: 'Annulé', cls: 'bg-red-100 text-red-700' }
  return { label: 'Terminé', cls: 'bg-green-100 text-green-700' }
}

const visibleMatches = computed(() => matches.value)

watch([showAll, statusFilter], load)
onMounted(load)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-bold">Matchs</h1>
      <div class="flex items-center gap-4">
        <label v-if="!auth.isAdmin" class="flex items-center gap-2 text-sm">
          <input v-model="showAll" type="checkbox" data-cy="show-all" />
          Voir tous les matchs
        </label>
        <select v-model="statusFilter" class="input w-auto" data-cy="status-filter">
          <option value="">Tous les statuts</option>
          <option value="A_VENIR">À venir</option>
          <option value="TERMINE">Terminé</option>
          <option value="ANNULE">Annulé</option>
        </select>
      </div>
    </div>

    <p v-if="loading" class="text-gray-500">Chargement…</p>
    <p v-else-if="visibleMatches.length === 0" class="text-gray-500" data-cy="no-matches">
      Aucun match à afficher.
    </p>

    <div v-else class="space-y-3" data-cy="matches-list">
      <div v-for="m in visibleMatches" :key="m.id" class="card" data-cy="match-row">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p class="text-sm text-gray-500">{{ formatDateTime(m.event) }} · Piste {{ m.court_number }}</p>
            <p class="mt-1 font-semibold">
              <!-- Interpolation = échappement automatique (protection XSS). -->
              <span data-cy="team1-company">{{ m.team1.company }}</span>
              <span class="mx-2 text-gray-400">vs</span>
              <span data-cy="team2-company">{{ m.team2.company }}</span>
            </p>
            <p class="text-sm text-gray-600">{{ playersOf(m.team1) }} — {{ playersOf(m.team2) }}</p>
          </div>
          <div class="text-right">
            <span class="badge" :class="statusBadge(m.status).cls">{{ statusBadge(m.status).label }}</span>
            <p v-if="m.status === 'TERMINE'" class="mt-1 text-sm font-medium">{{ m.score_team1 }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
