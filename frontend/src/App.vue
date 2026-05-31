<script setup>
import NavBar from './components/NavBar.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <NavBar />
    <main class="mx-auto max-w-6xl px-4 py-8">
      <router-view />
    </main>
  </div>
</template>
