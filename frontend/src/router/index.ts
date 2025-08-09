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
        redirect: (to) => {
          // Smart redirect based on auth state
          const authStore = useAuthStore()
          return authStore.isAuthenticated ? '/dashboard' : '/login'
        }
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

// Simplified navigation guards with debugging
router.beforeEach(async (to, from, next) => {
  console.log(`🔄 Navigating from "${from.path}" to "${to.path}"`)
  
  // Update page title
  document.title = to.meta?.title as string || 'Passive CAPTCHA Admin'
  
  // Get authentication state
  const authStore = useAuthStore()
  
  // TEMPORARY: Disable session restoration completely for debugging
  console.log('🚫 Session restoration DISABLED for debugging')
  /*
  // Skip session restoration if coming from login (we just authenticated)
  const comingFromLogin = from.path === '/login'
  
  // Ensure session restored exactly once (prevent race with login navigation)
  if (!authStore.initialized && !comingFromLogin) {
    console.log('📡 Session not initialized, restoring...')
    await authStore.restoreSession()
    console.log('📡 Session restoration complete, authenticated:', authStore.isAuthenticated)
  } else if (comingFromLogin) {
    console.log('📡 Coming from login page, skipping session restoration')
  } else {
    console.log('📡 Session already initialized, skipping restoration')
  }
  */
  
  const requiresAuth = to.meta?.requiresAuth
  const isAuthenticated = authStore.isAuthenticated
  
  console.log('🔐 Route guard check:', { 
    path: to.path,
    requiresAuth, 
    isAuthenticated,
    hasToken: !!authStore.token,
    hasUser: !!authStore.user
  })
  
  // Simple navigation logic
  if (requiresAuth === true && !isAuthenticated) {
    console.log('🚫 Redirecting to login - authentication required')
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    console.log('✅ Redirecting to dashboard - already authenticated')
    next('/dashboard')
  } else {
    console.log('✅ Navigation allowed')
    next()
  }
})

// Global after navigation hook
router.afterEach((to, from) => {
  // Analytics tracking can go here
  if (typeof gtag !== 'undefined') {
    gtag('config', 'GA_MEASUREMENT_ID', {
      page_title: to.meta?.title,
      page_location: to.fullPath
    })
  }
})

export default router