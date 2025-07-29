import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createHead } from '@vueuse/head'
import Toast from 'vue-toastification'
import router from '@/router'
import App from '@/App.vue'

// Styles
import '@/assets/styles/main.css'
import 'vue-toastification/dist/index.css'

// Create Vue app instance
const app = createApp(App)

// State management
const pinia = createPinia()
app.use(pinia)

// Router
app.use(router)

// Head management
const head = createHead()
app.use(head)

// Toast notifications
app.use(Toast, {
  position: 'top-right',
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false
})

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err, info)
  // You can send errors to a monitoring service here
}

// Performance measurement
if (process.env.NODE_ENV === 'development') {
  app.config.performance = true
}

// Mount the app
app.mount('#app') 