import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Lazy load layouts and pages
const RootLayout = () => import('@/app/layout.vue')
const AuthLayout = () => import('@/app/auth/layout.vue')
const DashboardLayout = () => import('@/app/dashboard/layout.vue')

// Auth pages
const LoginPage = () => import('@/app/auth/login/page.vue')

// Dashboard pages
const DashboardPage = () => import('@/app/dashboard/page.vue')
const WebsitesPage = () => import('@/app/dashboard/websites/page.vue')
const WebsiteDetailPage = () => import('@/app/dashboard/websites/[id]/page.vue')
const AnalyticsPage = () => import('@/app/dashboard/analytics/page.vue')
const SettingsPage = () => import('@/app/dashboard/settings/page.vue')
const ProfilePage = () => import('@/app/dashboard/profile/page.vue')

// Error pages
const NotFoundPage = () => import('@/app/errors/404/page.vue')

// Define routes
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: RootLayout,
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      // Auth routes
      {
        path: 'login',
        component: AuthLayout,
        children: [
          {
            path: '',
            name: 'Login',
            component: LoginPage,
            meta: {
              requiresAuth: false,
              title: 'Login - Passive CAPTCHA Admin'
            }
          }
        ]
      },
      // Dashboard routes
      {
        path: 'dashboard',
        component: DashboardLayout,
        meta: {
          requiresAuth: true
        },
        children: [
          {
            path: '',
            name: 'Dashboard',
            component: DashboardPage,
            meta: {
              title: 'Dashboard - Passive CAPTCHA Admin'
            }
          },
          {
            path: 'websites',
            name: 'Websites',
            component: WebsitesPage,
            meta: {
              title: 'Websites - Passive CAPTCHA Admin'
            }
          },
          {
            path: 'websites/:id',
            name: 'WebsiteDetail',
            component: WebsiteDetailPage,
            meta: {
              title: 'Website Details - Passive CAPTCHA Admin'
            }
          },
          {
            path: 'analytics',
            name: 'Analytics',
            component: AnalyticsPage,
            meta: {
              title: 'Analytics - Passive CAPTCHA Admin'
            }
          },
          {
            path: 'settings',
            name: 'Settings',
            component: SettingsPage,
            meta: {
              title: 'Settings - Passive CAPTCHA Admin'
            }
          },
          {
            path: 'profile',
            name: 'Profile',
            component: ProfilePage,
            meta: {
              title: 'Profile - Passive CAPTCHA Admin'
            }
          }
        ]
      },
      // 404 fallback
      {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: NotFoundPage,
        meta: {
          requiresAuth: false,
          title: 'Page Not Found - Passive CAPTCHA Admin'
        }
      }
    ]
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
  // Update page title
  document.title = to.meta?.title as string || 'Passive CAPTCHA Admin'
  
  // Check authentication
  const authStore = useAuthStore()
  
  if (import.meta.env.DEV) {
    console.log('[ROUTER DEBUG] Navigation to:', to.path, 'from:', from.path)
    console.log('[ROUTER DEBUG] Auth store initialized:', authStore.initialized)
  }
  
  // Only restore session if not already initialized
  if (!authStore.initialized) {
    if (import.meta.env.DEV) {
      console.log('[ROUTER DEBUG] Restoring session (first time)...')
    }
    await authStore.restoreSession()
    if (import.meta.env.DEV) {
      console.log('[ROUTER DEBUG] Session restored, authenticated:', authStore.isAuthenticated)
    }
  } else {
    if (import.meta.env.DEV) {
      console.log('[ROUTER DEBUG] Session already initialized, skipping restoration')
    }
  }
  
  const requiresAuth = to.meta?.requiresAuth
  const isAuthenticated = authStore.isAuthenticated
  
  if (import.meta.env.DEV) {
    console.log('[ROUTER DEBUG] Route requires auth:', requiresAuth)
    console.log('[ROUTER DEBUG] User authenticated:', isAuthenticated)
    console.log('[ROUTER DEBUG] Token exists:', !!authStore.token)
    console.log('[ROUTER DEBUG] User exists:', !!authStore.user)
    
    console.log('[ROUTER DEBUG] Navigation check:', { 
      to: to.path, 
      requiresAuth, 
      isAuthenticated,
      token: !!authStore.token,
      user: !!authStore.user,
      initialized: authStore.initialized
    })
  }
  
  // Proper router guard with fixed logic
  if (requiresAuth && !isAuthenticated) {
    if (import.meta.env.DEV) {
      console.log('[ROUTER DEBUG] Auth required but user not authenticated, redirecting to login')
    }
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    if (import.meta.env.DEV) {
      console.log('[ROUTER DEBUG] User authenticated but trying to access login, redirecting to dashboard')
    }
    next('/dashboard')
  } else {
    if (import.meta.env.DEV) {
      console.log('[ROUTER DEBUG] Allowing navigation')
    }
    next()
  }
})

// Global after navigation hook
router.afterEach((to, from) => {
  if (import.meta.env.DEV) {
    console.log('[ROUTER DEBUG] Navigation completed:', { from: from.path, to: to.path })
  }
  
  // You can add analytics tracking here
  if (typeof gtag !== 'undefined') {
    gtag('config', 'GA_MEASUREMENT_ID', {
      page_title: to.meta?.title,
      page_location: to.fullPath
    })
  }
})

export default router 