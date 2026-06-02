<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const matches = ref([])
const teams = ref([])
const loading = ref(true)
const error = ref('')
const notice = ref('')

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

function flashError(e) {
  const detail = e.response?.data?.detail
  error.value = typeof detail === 'string' ? detail : detail?.detail || 'Une erreur est survenue'
  notice.value = ''
  setTimeout(() => (error.value = ''), 6000)
}

function flashNotice(msg) {
  notice.value = msg
  error.value = ''
  setTimeout(() => (notice.value = ''), 4000)
}

async function load() {
  loading.value = true
  const params = {}
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

async function loadTeams() {
  if (!auth.isAdmin) return
  const { data } = await apiClient.get('/teams')
  teams.value = data.teams
}

const playersOf = (team) => team.players.map((p) => `${p.first_name} ${p.last_name}`).join(' & ')

const statusBadge = (status) => {
  if (status === 'A_VENIR') return { label: 'À venir', cls: 'bg-blue-100 text-blue-700' }
  if (status === 'ANNULE') return { label: 'Annulé', cls: 'bg-red-100 text-red-700' }
  return { label: 'Terminé', cls: 'bg-green-100 text-green-700' }
}

const visibleMatches = computed(() => matches.value)

// ── Création de match (admin) ──
const showForm = ref(false)
const today = new Date().toISOString().slice(0, 10)
const newMatch = ref({ event_date: '', event_time: '', court_number: 1, team1_id: '', team2_id: '' })

async function createMatch() {
  try {
    await apiClient.post('/matches', {
      event_date: newMatch.value.event_date,
      event_time: newMatch.value.event_time,
      court_number: Number(newMatch.value.court_number),
      team1_id: Number(newMatch.value.team1_id),
      team2_id: Number(newMatch.value.team2_id),
    })
    newMatch.value = { event_date: '', event_time: '', court_number: 1, team1_id: '', team2_id: '' }
    showForm.value = false
    flashNotice('Match créé avec succès.')
    await load()
  } catch (e) {
    flashError(e)
  }
}

// ── Saisie de score / suppression (admin) ──
async function enterScore(m) {
  const score1 = window.prompt(
    `Score de ${m.team1.company} (ex: 6-4, 6-3) :`,
    m.score_team1 || '',
  )
  if (score1 === null) return
  const score2 = window.prompt(
    `Score de ${m.team2.company} (ex: 4-6, 3-6) :`,
    m.score_team2 || '',
  )
  if (score2 === null) return
  try {
    await apiClient.put(`/matches/${m.id}`, {
      status: 'TERMINE',
      score_team1: score1,
      score_team2: score2,
    })
    flashNotice('Score enregistré.')
    await load()
  } catch (e) {
    flashError(e)
  }
}

async function cancelMatch(m) {
  if (!confirm(`Annuler le match ${m.team1.company} vs ${m.team2.company} ?`)) return
  try {
    await apiClient.put(`/matches/${m.id}`, { status: 'ANNULE' })
    flashNotice('Match annulé.')
    await load()
  } catch (e) {
    flashError(e)
  }
}

async function deleteMatch(m) {
  if (!confirm(`Supprimer définitivement ce match ?`)) return
  try {
    await apiClient.delete(`/matches/${m.id}`)
    flashNotice('Match supprimé.')
    await load()
  } catch (e) {
    flashError(e)
  }
}

watch([showAll, statusFilter], load)
onMounted(() => {
  load()
  loadTeams()
})
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
        <button v-if="auth.isAdmin" class="btn-primary" data-cy="new-match" @click="showForm = !showForm">
          {{ showForm ? 'Fermer' : '+ Nouveau match' }}
        </button>
      </div>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700" data-cy="match-error">{{ error }}</p>
    <p v-if="notice" class="mb-4 rounded bg-green-50 px-3 py-2 text-sm text-green-700" data-cy="match-notice">{{ notice }}</p>

    <!-- Formulaire de création (admin) -->
    <div v-if="auth.isAdmin && showForm" class="card mb-6">
      <h2 class="mb-3 font-semibold">Nouveau match</h2>
      <form @submit.prevent="createMatch" class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-sm font-medium">Date</label>
          <input v-model="newMatch.event_date" type="date" :min="today" class="input" data-cy="m-date" required />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Heure (HH:MM)</label>
          <input v-model="newMatch.event_time" type="time" class="input" data-cy="m-time" required />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Piste (1-10)</label>
          <input v-model="newMatch.court_number" type="number" min="1" max="10" class="input" data-cy="m-court" required />
        </div>
        <div></div>
        <div>
          <label class="mb-1 block text-sm font-medium">Équipe 1</label>
          <select v-model="newMatch.team1_id" class="input" data-cy="m-team1" required>
            <option value="">Sélectionner…</option>
            <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.company }} ({{ playersOf(t) }})</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Équipe 2</label>
          <select v-model="newMatch.team2_id" class="input" data-cy="m-team2" required>
            <option value="">Sélectionner…</option>
            <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.company }} ({{ playersOf(t) }})</option>
          </select>
        </div>
        <div class="sm:col-span-2">
          <button type="submit" class="btn-primary" data-cy="m-submit">Créer le match</button>
        </div>
      </form>
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
              <span data-cy="team1-company" v-html="m.team1.company"></span>
              <span class="mx-2 text-gray-400">vs</span>
              <span data-cy="team2-company" v-html="m.team2.company"></span>
            </p>
            <p class="text-sm text-gray-600">{{ playersOf(m.team1) }} — {{ playersOf(m.team2) }}</p>
          </div>
          <div class="text-right">
            <span class="badge" :class="statusBadge(m.status).cls">{{ statusBadge(m.status).label }}</span>
            <p v-if="m.status === 'TERMINE'" class="mt-1 text-sm font-medium">{{ m.score_team1 }}</p>

            <!-- Actions admin -->
            <div v-if="auth.isAdmin" class="mt-2 flex justify-end gap-3 text-sm">
              <button class="text-padel-600 hover:underline" data-cy="m-score" @click="enterScore(m)">Saisir le score</button>
              <button v-if="m.status === 'A_VENIR'" class="text-amber-600 hover:underline" @click="cancelMatch(m)">Annuler</button>
              <button class="text-red-600 hover:underline" data-cy="m-delete" @click="deleteMatch(m)">Supprimer</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
