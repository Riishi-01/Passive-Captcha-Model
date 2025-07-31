<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-300">
    <!-- Header -->
    <div class="flex items-center space-x-3 mb-4">
      <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
        <component :is="iconComponent" class="h-5 w-5 text-gray-600 dark:text-gray-400" />
      </div>
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ title }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {{ subtitle }}
        </p>
      </div>
    </div>

    <!-- Content Slot -->
    <div class="space-y-3">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  GlobeAltIcon,
  ShieldExclamationIcon,
  CpuChipIcon,
  ClockIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'

interface Props {
  title: string
  subtitle: string
  icon: 'globe' | 'shield-exclamation' | 'cpu-chip' | 'clock' | 'chart-bar'
}

const props = defineProps<Props>()

// Icon mapping
const iconMap = {
  'globe': GlobeAltIcon,
  'shield-exclamation': ShieldExclamationIcon,
  'cpu-chip': CpuChipIcon,
  'clock': ClockIcon,
  'chart-bar': ChartBarIcon
}

// Computed
const iconComponent = computed(() => iconMap[props.icon])
</script>

<style scoped>
/* Analytics card animations */
.space-y-3 > * {
  animation: slideInUp 0.6s ease-out;
  animation-fill-mode: both;
}

.space-y-3 > *:nth-child(1) { animation-delay: 0.1s; }
.space-y-3 > *:nth-child(2) { animation-delay: 0.2s; }
.space-y-3 > *:nth-child(3) { animation-delay: 0.3s; }
.space-y-3 > *:nth-child(4) { animation-delay: 0.4s; }
.space-y-3 > *:nth-child(5) { animation-delay: 0.5s; }

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>