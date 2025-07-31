<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Model Accuracy
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          False positives & negatives tracking
        </p>
      </div>
      
      <div class="flex items-center space-x-2">
        <div class="text-right">
          <div class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ data.f1Score }}%
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            F1 Score
          </div>
        </div>
      </div>
    </div>

    <!-- Confusion Matrix Visualization -->
    <div class="mb-6">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Confusion Matrix</h4>
      <div class="grid grid-cols-2 gap-2 max-w-xs mx-auto">
        <!-- True Positives -->
        <div class="p-4 bg-green-100 dark:bg-green-900/20 rounded-lg text-center">
          <div class="text-xl font-bold text-green-700 dark:text-green-400">
            {{ formatNumber(data.truePositives) }}
          </div>
          <div class="text-xs text-green-600 dark:text-green-500 font-medium">
            True Positives
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            Correctly identified bots
          </div>
        </div>

        <!-- False Positives -->
        <div class="p-4 bg-red-100 dark:bg-red-900/20 rounded-lg text-center">
          <div class="text-xl font-bold text-red-700 dark:text-red-400">
            {{ formatNumber(data.falsePositives) }}
          </div>
          <div class="text-xs text-red-600 dark:text-red-500 font-medium">
            False Positives
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            Humans marked as bots
          </div>
        </div>

        <!-- False Negatives -->
        <div class="p-4 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg text-center">
          <div class="text-xl font-bold text-yellow-700 dark:text-yellow-400">
            {{ formatNumber(data.falseNegatives) }}
          </div>
          <div class="text-xs text-yellow-600 dark:text-yellow-500 font-medium">
            False Negatives
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            Bots marked as humans
          </div>
        </div>

        <!-- True Negatives -->
        <div class="p-4 bg-blue-100 dark:bg-blue-900/20 rounded-lg text-center">
          <div class="text-xl font-bold text-blue-700 dark:text-blue-400">
            {{ formatNumber(data.trueNegatives) }}
          </div>
          <div class="text-xs text-blue-600 dark:text-blue-500 font-medium">
            True Negatives
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            Correctly identified humans
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Metrics -->
    <div class="space-y-4">
      <!-- Precision -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Precision</span>
          <span class="text-xs text-gray-500 dark:text-gray-400">(TP / TP + FP)</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-32 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
            <div 
              class="h-full bg-purple-500 rounded-full transition-all duration-1000"
              :style="{ width: `${data.precision}%` }"
            ></div>
          </div>
          <span class="text-sm font-semibold text-gray-900 dark:text-white w-12 text-right">
            {{ data.precision }}%
          </span>
        </div>
      </div>

      <!-- Recall -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-cyan-500 rounded-full"></div>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Recall</span>
          <span class="text-xs text-gray-500 dark:text-gray-400">(TP / TP + FN)</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-32 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
            <div 
              class="h-full bg-cyan-500 rounded-full transition-all duration-1000"
              :style="{ width: `${data.recall}%` }"
            ></div>
          </div>
          <span class="text-sm font-semibold text-gray-900 dark:text-white w-12 text-right">
            {{ data.recall }}%
          </span>
        </div>
      </div>

      <!-- F1 Score -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-green-500 rounded-full"></div>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">F1 Score</span>
          <span class="text-xs text-gray-500 dark:text-gray-400">(Harmonic Mean)</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-32 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
            <div 
              class="h-full bg-green-500 rounded-full transition-all duration-1000"
              :style="{ width: `${data.f1Score}%` }"
            ></div>
          </div>
          <span class="text-sm font-semibold text-gray-900 dark:text-white w-12 text-right">
            {{ data.f1Score }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Accuracy Summary -->
    <div class="mt-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Overall Accuracy
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            (TP + TN) / Total Predictions
          </div>
        </div>
        <div :class="[
          'text-2xl font-bold',
          overallAccuracy >= 95 ? 'text-green-600 dark:text-green-400' :
          overallAccuracy >= 90 ? 'text-blue-600 dark:text-blue-400' :
          overallAccuracy >= 80 ? 'text-yellow-600 dark:text-yellow-400' :
          'text-red-600 dark:text-red-400'
        ]">
          {{ overallAccuracy }}%
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: {
    falsePositives: number
    falseNegatives: number
    truePositives: number
    trueNegatives: number
    precision: number
    recall: number
    f1Score: number
  }
}

const props = defineProps<Props>()

// Computed metrics
const overallAccuracy = computed(() => {
  const total = props.data.truePositives + props.data.trueNegatives + 
                props.data.falsePositives + props.data.falseNegatives
  
  if (total === 0) return 0
  
  const correct = props.data.truePositives + props.data.trueNegatives
  return Math.round((correct / total) * 100)
})

// Methods
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}
</script>

<style scoped>
/* Animation for confusion matrix */
.grid > div {
  animation: fadeInScale 0.6s ease-out;
  animation-fill-mode: both;
}

.grid > div:nth-child(1) { animation-delay: 0.1s; }
.grid > div:nth-child(2) { animation-delay: 0.2s; }
.grid > div:nth-child(3) { animation-delay: 0.3s; }
.grid > div:nth-child(4) { animation-delay: 0.4s; }

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Progress bar animations */
.transition-all {
  animation-delay: 0.5s;
}
</style>