<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import apiClient from '../api/client'

const profile = ref(null)
const form = ref({ first_name: '', last_name: '', email: '', birth_date: '' })
const message = ref('')
const error = ref('')
const loading = ref(true)

async function load() {
  loading.value = true
  const { data } = await apiClient.get('/profile/me')
  profile.value = data
  if (data.player) {
    form.value = {
      first_name: data.player.first_name,
      last_name: data.player.last_name,
      email: data.user.email,
      birth_date: data.player.birth_date || '',
    }
  } else {
    form.value.email = data.user.email
  }
  loading.value = false
}

async function save() {
  message.value = ''
  error.value = ''
  try {
    const payload = {
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      email: form.value.email,
      birth_date: form.value.birth_date || null,
    }
    await apiClient.put('/profile/me', payload)
    message.value = 'Profil mis à jour.'
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur lors de la mise à jour'
  }
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <h1 class="mb-6 text-2xl font-bold">Mon profil</h1>

    <div v-if="profile" class="card">
      <form @submit.prevent="save" class="space-y-4">
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-sm font-medium">Prénom</label>
            <input v-model="form.first_name" class="input" data-cy="first-name" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium">Nom</label>
            <input v-model="form.last_name" class="input" data-cy="last-name" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Email</label>
          <input v-model="form.email" type="email" class="input" data-cy="email" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Date de naissance</label>
          <input v-model="form.birth_date" type="date" class="input" data-cy="birth-date" />
        </div>
        <div v-if="profile.player">
          <label class="mb-1 block text-sm font-medium">N° de licence (lecture seule)</label>
          <input :value="profile.player.license_number" class="input bg-gray-100" disabled />
        </div>

        <p v-if="message" class="rounded bg-green-50 px-3 py-2 text-sm text-green-700" data-cy="success">{{ message }}</p>
        <p v-if="error" class="rounded bg-red-50 px-3 py-2 text-sm text-red-700" data-cy="error">{{ error }}</p>

        <div class="flex items-center justify-between">
          <button type="submit" class="btn-primary" data-cy="save">Enregistrer</button>
          <RouterLink to="/change-password" class="text-sm text-padel-600 hover:underline">
            Changer mon mot de passe
          </RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>
