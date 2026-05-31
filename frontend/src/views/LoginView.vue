<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const attemptsRemaining = ref(null)
const loading = ref(false)

async function submit() {
  error.value = ''
  attemptsRemaining.value = null
  loading.value = true
  try {
    const data = await auth.login(email.value, password.value)
    if (data.user?.must_change_password) {
      router.push({ name: 'change-password' })
    } else {
      router.push(route.query.redirect || { name: 'home' })
    }
  } catch (e) {
    const detail = e.response?.data?.detail
    if (detail && typeof detail === 'object') {
      error.value = detail.detail || 'Erreur de connexion'
      if (typeof detail.attempts_remaining === 'number') {
        attemptsRemaining.value = detail.attempts_remaining
      }
      if (typeof detail.minutes_remaining === 'number') {
        error.value = `Compte bloqué. Réessayez dans ${detail.minutes_remaining} minute(s).`
      }
    } else {
      error.value = detail || 'Erreur de connexion'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md">
    <div class="card">
      <div class="mb-6 text-center">
        <div class="text-4xl">🎾</div>
        <h1 class="mt-2 text-2xl font-bold text-padel-600">Connexion</h1>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium">Email</label>
          <input v-model="email" type="email" class="input" required data-cy="email" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">Mot de passe</label>
          <input v-model="password" type="password" class="input" required data-cy="password" />
        </div>

        <p v-if="error" class="rounded bg-red-50 px-3 py-2 text-sm text-red-700" data-cy="login-error">
          {{ error }}
        </p>
        <p v-if="attemptsRemaining !== null" class="text-sm text-gray-600" data-cy="attempts">
          Tentatives restantes : {{ attemptsRemaining }}
        </p>

        <button type="submit" class="w-full btn-primary" :disabled="loading" data-cy="submit">
          {{ loading ? 'Connexion…' : 'Se connecter' }}
        </button>
      </form>
    </div>
  </div>
</template>
