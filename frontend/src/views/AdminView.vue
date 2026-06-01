<script setup>
import { computed, onMounted, ref } from 'vue'
import apiClient from '../api/client'

const tab = ref('players')
const tabs = [
  { id: 'players', label: 'Joueurs' },
  { id: 'teams', label: 'Équipes' },
  { id: 'pools', label: 'Poules' },
  { id: 'accounts', label: 'Comptes' },
]

const players = ref([])
const teams = ref([])
const pools = ref([])
const error = ref('')
const notice = ref('')

function flashError(e) {
  error.value = e.response?.data?.detail || 'Une erreur est survenue'
  setTimeout(() => (error.value = ''), 5000)
}

async function loadAll() {
  const [p, t, po] = await Promise.all([
    apiClient.get('/players'),
    apiClient.get('/teams'),
    apiClient.get('/pools'),
  ])
  players.value = p.data.players
  teams.value = t.data.teams
  pools.value = po.data.pools
}

// ── Joueurs ──
const newPlayer = ref({ first_name: '', last_name: '', company: '', license_number: '', email: '' })
async function addPlayer() {
  try {
    await apiClient.post('/players', newPlayer.value)
    newPlayer.value = { first_name: '', last_name: '', company: '', license_number: '', email: '' }
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}
async function deletePlayer(id) {
  if (!confirm('Attention, cette action est irréversible. Supprimer ce joueur ?')) return
  try {
    await apiClient.delete(`/players/${id}`)
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}

// ── Équipes ──
const newTeam = ref({ company: '', player1_id: '', player2_id: '', pool_id: '' })
async function addTeam() {
  try {
    await apiClient.post('/teams', {
      company: newTeam.value.company,
      player1_id: Number(newTeam.value.player1_id),
      player2_id: Number(newTeam.value.player2_id),
      pool_id: newTeam.value.pool_id ? Number(newTeam.value.pool_id) : null,
    })
    newTeam.value = { company: '', player1_id: '', player2_id: '', pool_id: '' }
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}
async function deleteTeam(id) {
  if (!confirm('Supprimer cette équipe ?')) return
  try {
    await apiClient.delete(`/teams/${id}`)
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}

// ── Poules ──
const newPool = ref({ name: '', team_ids: [] })
async function addPool() {
  try {
    await apiClient.post('/pools', { name: newPool.value.name, team_ids: newPool.value.team_ids.map(Number) })
    newPool.value = { name: '', team_ids: [] }
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}
async function deletePool(id) {
  if (!confirm('Supprimer cette poule ?')) return
  try {
    await apiClient.delete(`/pools/${id}`)
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}

// ── Comptes ──
const playersWithoutAccount = computed(() => players.value.filter((p) => !p.has_account))
const selectedPlayerForAccount = ref('')
const tempPassword = ref('')
async function createAccount() {
  tempPassword.value = ''
  try {
    const { data } = await apiClient.post('/admin/accounts/create', {
      player_id: Number(selectedPlayerForAccount.value),
      role: 'JOUEUR',
    })
    tempPassword.value = data.temporary_password
    notice.value = `Compte créé pour ${data.email}.`
    selectedPlayerForAccount.value = ''
    await loadAll()
  } catch (e) {
    flashError(e)
  }
}

onMounted(loadAll)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">Administration</h1>

    <div class="mb-4 flex gap-2 border-b border-gray-200">
      <button
        v-for="t in tabs"
        :key="t.id"
        class="-mb-px border-b-2 px-4 py-2 text-sm font-medium"
        :class="tab === t.id ? 'border-padel-600 text-padel-600' : 'border-transparent text-gray-500'"
        :data-cy="`tab-${t.id}`"
        @click="tab = t.id"
      >
        {{ t.label }}
      </button>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700" data-cy="admin-error">{{ error }}</p>

    <!-- JOUEURS -->
    <section v-show="tab === 'players'">
      <div class="card mb-4">
        <h2 class="mb-3 font-semibold">Nouveau joueur</h2>
        <form @submit.prevent="addPlayer" class="grid gap-3 sm:grid-cols-2">
          <input v-model="newPlayer.first_name" class="input" placeholder="Prénom" data-cy="p-first" />
          <input v-model="newPlayer.last_name" class="input" placeholder="Nom" data-cy="p-last" />
          <input v-model="newPlayer.company" class="input" placeholder="Entreprise" data-cy="p-company" />
          <input v-model="newPlayer.license_number" class="input" placeholder="Licence (LXXXXXX)" data-cy="p-license" />
          <input v-model="newPlayer.email" class="input" placeholder="Email" data-cy="p-email" />
          <button type="submit" class="btn-primary" data-cy="p-submit">Ajouter</button>
        </form>
      </div>
      <div class="card">
        <table class="w-full text-sm" data-cy="players-table">
          <thead class="text-left text-gray-500">
            <tr><th class="py-2">Nom</th><th>Entreprise</th><th>Licence</th><th>Compte</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="p in players" :key="p.id" class="border-t border-gray-100">
              <td class="py-2">{{ p.first_name }} {{ p.last_name }}</td>
              <td>{{ p.company }}</td>
              <td>{{ p.license_number }}</td>
              <td>{{ p.has_account ? '✅' : '—' }}</td>
              <td class="text-right">
                <button class="text-red-600 hover:underline" @click="deletePlayer(p.id)">Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ÉQUIPES -->
    <section v-show="tab === 'teams'">
      <div class="card mb-4">
        <h2 class="mb-3 font-semibold">Nouvelle équipe</h2>
        <form @submit.prevent="addTeam" class="grid gap-3 sm:grid-cols-2">
          <input v-model="newTeam.company" class="input" placeholder="Entreprise" data-cy="t-company" />
          <select v-model="newTeam.player1_id" class="input" data-cy="t-p1">
            <option value="">Joueur 1</option>
            <option v-for="p in players" :key="p.id" :value="p.id">{{ p.first_name }} {{ p.last_name }} ({{ p.company }})</option>
          </select>
          <select v-model="newTeam.player2_id" class="input" data-cy="t-p2">
            <option value="">Joueur 2</option>
            <option v-for="p in players" :key="p.id" :value="p.id">{{ p.first_name }} {{ p.last_name }} ({{ p.company }})</option>
          </select>
          <select v-model="newTeam.pool_id" class="input" data-cy="t-pool">
            <option value="">Sans poule</option>
            <option v-for="po in pools" :key="po.id" :value="po.id">{{ po.name }}</option>
          </select>
          <button type="submit" class="btn-primary" data-cy="t-submit">Ajouter</button>
        </form>
      </div>
      <div class="card">
        <table class="w-full text-sm" data-cy="teams-table">
          <thead class="text-left text-gray-500"><tr><th class="py-2">Entreprise</th><th>Joueurs</th><th>Poule</th><th></th></tr></thead>
          <tbody>
            <tr v-for="t in teams" :key="t.id" class="border-t border-gray-100">
              <td class="py-2" v-html="t.company"></td>
              <td>{{ t.players.map((p) => p.first_name + ' ' + p.last_name).join(' & ') }}</td>
              <td>{{ t.pool ? t.pool.name : '—' }}</td>
              <td class="text-right"><button class="text-red-600 hover:underline" @click="deleteTeam(t.id)">Supprimer</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- POULES -->
    <section v-show="tab === 'pools'">
      <div class="card mb-4">
        <h2 class="mb-3 font-semibold">Nouvelle poule (exactement 6 équipes)</h2>
        <form @submit.prevent="addPool" class="space-y-3">
          <input v-model="newPool.name" class="input" placeholder="Nom (ex: Poule A)" data-cy="pool-name" />
          <select v-model="newPool.team_ids" multiple class="input h-40" data-cy="pool-teams">
            <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.company }} ({{ t.players.map((p) => p.first_name).join(' & ') }})</option>
          </select>
          <p class="text-xs text-gray-500">{{ newPool.team_ids.length }} équipe(s) sélectionnée(s) — il en faut 6.</p>
          <button type="submit" class="btn-primary" data-cy="pool-submit">Créer la poule</button>
        </form>
      </div>
      <div class="card">
        <div v-for="po in pools" :key="po.id" class="mb-3 border-b border-gray-100 pb-3">
          <div class="flex items-center justify-between">
            <p class="font-medium">{{ po.name }} <span class="text-sm text-gray-500">({{ po.teams_count }} équipes)</span></p>
            <button class="text-red-600 hover:underline" @click="deletePool(po.id)">Supprimer</button>
          </div>
          <p class="mt-1 text-sm text-gray-600">{{ po.teams.map((t) => t.company).join(', ') }}</p>
        </div>
        <p v-if="pools.length === 0" class="text-sm text-gray-500">Aucune poule.</p>
      </div>
    </section>

    <!-- COMPTES -->
    <section v-show="tab === 'accounts'">
      <div class="card mb-4">
        <h2 class="mb-3 font-semibold">Créer un compte joueur</h2>
        <form @submit.prevent="createAccount" class="flex flex-wrap items-end gap-3">
          <select v-model="selectedPlayerForAccount" class="input w-auto" data-cy="acc-player">
            <option value="">Joueur sans compte…</option>
            <option v-for="p in playersWithoutAccount" :key="p.id" :value="p.id">
              {{ p.first_name }} {{ p.last_name }} ({{ p.company }})
            </option>
          </select>
          <button type="submit" class="btn-primary" :disabled="!selectedPlayerForAccount" data-cy="acc-submit">
            Créer le compte
          </button>
        </form>
        <div v-if="tempPassword" class="mt-4 rounded bg-yellow-50 px-3 py-2 text-sm" data-cy="temp-password">
          <p class="font-medium">{{ notice }}</p>
          <p>Mot de passe temporaire (affiché une seule fois) : <code class="font-mono">{{ tempPassword }}</code></p>
        </div>
      </div>
    </section>
  </div>
</template>
