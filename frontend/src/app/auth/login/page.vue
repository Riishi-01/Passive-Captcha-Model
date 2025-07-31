<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        Sign in to your account
      </h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Access your admin dashboard
      </p>
    </div>

    <!-- Login Form -->
    <LoginForm />

    <!-- System Status -->
    <SystemStatus />
  </div>
</template>

<script setup lang="ts">
import LoginForm from './_components/LoginForm.vue'
import SystemStatus from './_components/SystemStatus.vue'
</script>