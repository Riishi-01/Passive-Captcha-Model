<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <KPICard
      title="Total Verifications"
      :value="stats.totalVerifications"
      :change="stats.verificationChange"
      icon="shield-check"
      color="primary"
    />
    <KPICard
      title="Human Rate"
      :value="`${stats.humanRate}%`"
      :change="stats.humanRateChange"
      icon="user-check"
      color="success"
    />
    <KPICard
      title="Avg Confidence"
      :value="`${stats.avgConfidence}%`"
      :change="stats.confidenceChange"
      icon="chart-bar"
      color="warning"
    />
    <KPICard
      title="Response Time"
      :value="`${stats.avgResponseTime}ms`"
      :change="stats.responseTimeChange"
      icon="clock"
      color="info"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '../_stores/useDashboard'
import KPICard from './KPICard.vue'

// Store
const dashboardStore = useDashboardStore()

// Computed
const stats = computed(() => dashboardStore.stats)
</script>

<style scoped>
/* KPI Section animations */
.grid {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stagger animation for cards */
.grid > :nth-child(1) { animation-delay: 0.1s; }
.grid > :nth-child(2) { animation-delay: 0.2s; }
.grid > :nth-child(3) { animation-delay: 0.3s; }
.grid > :nth-child(4) { animation-delay: 0.4s; }
</style>