<script setup>
import { computed, onMounted, ref } from 'vue'
import apiClient from '../api/client'

const events = ref([])
const current = ref(new Date())
const selectedDate = ref(null)
const loading = ref(true)

const monthLabel = computed(() =>
  current.value.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' }),
)

function ymd(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function load() {
  loading.value = true
  const month = `${current.value.getFullYear()}-${String(current.value.getMonth() + 1).padStart(2, '0')}`
  try {
    const { data } = await apiClient.get('/events', { params: { month } })
    events.value = data.events
  } finally {
    loading.value = false
  }
}

const eventsByDate = computed(() => {
  const map = {}
  for (const e of events.value) {
    ;(map[e.event_date] ||= []).push(e)
  }
  return map
})

const calendarDays = computed(() => {
  const year = current.value.getFullYear()
  const month = current.value.getMonth()
  const first = new Date(year, month, 1)
  const startOffset = (first.getDay() + 6) % 7 // lundi = 0
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells = []
  for (let i = 0; i < startOffset; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(year, month, d))
  return cells
})

const selectedEvents = computed(() =>
  selectedDate.value ? eventsByDate.value[selectedDate.value] || [] : [],
)

function changeMonth(delta) {
  current.value = new Date(current.value.getFullYear(), current.value.getMonth() + delta, 1)
  selectedDate.value = null
  load()
}

function selectDay(day) {
  if (day) selectedDate.value = ymd(day)
}

onMounted(load)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold">Planning</h1>

    <div class="card">
      <div class="mb-4 flex items-center justify-between">
        <button class="btn-secondary" @click="changeMonth(-1)">‹ Mois précédent</button>
        <h2 class="text-lg font-semibold capitalize" data-cy="month-label">{{ monthLabel }}</h2>
        <button class="btn-secondary" @click="changeMonth(1)">Mois suivant ›</button>
      </div>

      <div class="grid grid-cols-7 gap-1 text-center text-xs font-medium text-gray-500">
        <div v-for="(d, i) in ['L', 'M', 'M', 'J', 'V', 'S', 'D']" :key="i">{{ d }}</div>
      </div>
      <div class="mt-1 grid grid-cols-7 gap-1">
        <button
          v-for="(day, i) in calendarDays"
          :key="i"
          :disabled="!day"
          class="relative aspect-square rounded p-1 text-sm"
          :class="[
            day ? 'hover:bg-padel-50' : 'cursor-default',
            day && ymd(day) === selectedDate ? 'bg-padel-600 text-white' : '',
          ]"
          @click="selectDay(day)"
        >
          <template v-if="day">
            {{ day.getDate() }}
            <span
              v-if="eventsByDate[ymd(day)]"
              class="absolute bottom-1 left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-orange-400"
              data-cy="event-dot"
            ></span>
          </template>
        </button>
      </div>
    </div>

    <div v-if="selectedDate" class="mt-6">
      <h3 class="mb-3 font-semibold">Événements du {{ selectedDate }}</h3>
      <p v-if="selectedEvents.length === 0" class="text-sm text-gray-500">Aucun événement ce jour.</p>
      <div v-for="ev in selectedEvents" :key="ev.id" class="card mb-3">
        <p class="font-medium">🕒 {{ ev.event_time }}</p>
        <ul class="mt-2 space-y-1 text-sm">
          <li v-for="m in ev.matches" :key="m.id" class="flex items-center gap-2">
            <span class="badge bg-gray-100 text-gray-700">Piste {{ m.court_number }}</span>
            <span>{{ m.team1.company }} vs {{ m.team2.company }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
