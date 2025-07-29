import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Lazy load components for better performance
const Dashboard = () => import('@/views/Dashboard.vue')
const Login = () => import('@/views/auth/Login.vue')
const Websites = () => import('@/views/websites/Websites.vue')
const WebsiteDetail = () => import('@/views/websites/WebsiteDetail.vue')
const Analytics = () => import('@/views/analytics/Analytics.vue')
const Logs = () => import('@/views/logs/Logs.vue')
const Settings = () => import('@/views/settings/Settings.vue')
const Profile = () => import('@/views/profile/Profile.vue')
const NotFound = () => import('@/views/errors/NotFound.vue')

// Define routes
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      requiresAuth: false,
      title: 'Login - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      requiresAuth: true,
      title: 'Dashboard - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/websites',
    name: 'Websites',
    component: Websites,
    meta: {
      requiresAuth: true,
      title: 'Websites - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/websites/:id',
    name: 'WebsiteDetail',
    component: WebsiteDetail,
    meta: {
      requiresAuth: true,
      title: 'Website Details - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: Analytics,
    meta: {
      requiresAuth: true,
      title: 'Analytics - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs,
    meta: {
      requiresAuth: true,
      title: 'Logs - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      requiresAuth: true,
      title: 'Settings - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: {
      requiresAuth: true,
      title: 'Profile - Passive CAPTCHA Admin'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      requiresAuth: false,
      title: 'Page Not Found - Passive CAPTCHA Admin'
    }
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0 }
  }
})

// Global navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Update page title
  document.title = to.meta?.title as string || 'Passive CAPTCHA Admin'
  
  // Check if route requires authentication
  if (to.meta?.requiresAuth) {
    // Check if user is authenticated
    if (!authStore.isAuthenticated) {
      // Try to restore session from localStorage
      await authStore.restoreSession()
      
      if (!authStore.isAuthenticated) {
        // Redirect to login with return URL
        next({
          name: 'Login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
  }
  
  // If user is authenticated and trying to access login page
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }
  
  next()
})

// Global after navigation hook
router.afterEach((to, from) => {
  // You can add analytics tracking here
  if (typeof gtag !== 'undefined') {
    gtag('config', 'GA_MEASUREMENT_ID', {
      page_title: to.meta?.title,
      page_location: to.fullPath
    })
  }
})

export default router 