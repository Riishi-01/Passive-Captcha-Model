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
// const LogsPage = () => import('@/app/dashboard/logs/page.vue') // Commented out - file missing
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
          // Logs route temporarily disabled - missing component
          // {
          //   path: 'logs',
          //   name: 'Logs', 
          //   component: LogsPage,
          //   meta: {
          //     title: 'Logs - Passive CAPTCHA Admin'
          //   }
          // },
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
  
  // Initialize auth store if not done yet
  if (!authStore.initialized) {
    await authStore.restoreSession()
  }
  
  const requiresAuth = to.meta?.requiresAuth
  const isAuthenticated = authStore.isAuthenticated
  
  if (requiresAuth && !isAuthenticated) {
    // Redirect to login if authentication is required but user is not authenticated
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    // Redirect to dashboard if user is already authenticated and tries to access login
    next('/dashboard')
  } else {
    next()
  }
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