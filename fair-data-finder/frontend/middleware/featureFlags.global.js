import { createError, defineNuxtRouteMiddleware } from '#app'
import { useConfigStore } from '~/stores/config'

const ADMIN_ROUTES = [ '/domains', '/groups', '/keywords' ]

export default defineNuxtRouteMiddleware((to) => {
  const config = useConfigStore()

  // The item detail page is public and independent of the Register tab.
  const isPublicItemView = /^\/register\/[^/]+\/view\/?$/.test(to.path)

  const registerBlocked = !config.registerTabEnabled
    && to.path.startsWith('/register')
    && !isPublicItemView

  const adminBlocked = !config.adminTabsEnabled
    && ADMIN_ROUTES.some(p => to.path === p || to.path.startsWith(`${ p }/`))

  if (registerBlocked || adminBlocked) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found' })
  }
})
