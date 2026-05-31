<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../api/client'

const router = useRouter()
const form = ref({ current_password: '', new_password: '', confirm_password: '' })
const message = ref('')
const error = ref('')

async function submit() {
  message.value = ''
  error.value = ''
  try {
    await apiClient.post('/auth/change-password', form.value)
    message.value = 'Mot de passe modifié avec succès.'
    setTimeout(() => router.push({ name: 'profile' }), 1000)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur lors du changement de mot de passe'
  }
}
</script>

<template>
  <div class="mx-auto max-w-md">
    <h1 class="mb-6 text-2xl font-bold">Changer mon mot de passe</h1>
    <div class="card">
      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium">Mot de passe actuel</label>
          <input v-model="form.current_password" type="password" class="input" data-cy="current" required />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Nouveau mot de passe</label>
          <input v-model="form.new_password" type="password" class="input" data-cy="new" required />
          <p class="mt-1 text-xs text-gray-500">
            Min. 12 caractères, avec majuscule, minuscule, chiffre et caractère spécial.
          </p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Confirmer le nouveau mot de passe</label>
          <input v-model="form.confirm_password" type="password" class="input" data-cy="confirm" required />
        </div>

        <p v-if="message" class="rounded bg-green-50 px-3 py-2 text-sm text-green-700" data-cy="success">{{ message }}</p>
        <p v-if="error" class="rounded bg-red-50 px-3 py-2 text-sm text-red-700" data-cy="error">{{ error }}</p>

        <button type="submit" class="w-full btn-primary" data-cy="submit">Changer le mot de passe</button>
      </form>
    </div>
  </div>
</template>
