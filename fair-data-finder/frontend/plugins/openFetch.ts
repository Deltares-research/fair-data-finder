export default defineNuxtPlugin((nuxtApp) => {
  // Browser requests keep the relative '/api' base so the reverse proxy in
  // front of Nuxt routes them. During SSR nothing sits in front of Nitro, so
  // the request has to address the backend directly.
  if (!import.meta.server) return

  const { internalApiBaseUrl } = useRuntimeConfig()

  // Without a configured address, leave the relative base in place so requests
  // keep falling through to the existing /api route rule.
  if (!internalApiBaseUrl) return

  // h3 only inherits the incoming request's headers when the target is a
  // relative URL. Addressing the backend directly makes the URL absolute, so
  // the session cookie has to be attached here or SSR requests are anonymous.
  const { cookie } = useRequestHeaders(['cookie'])

  nuxtApp.hook('openFetch:onRequest:api', (ctx) => {
    ctx.options.baseURL = internalApiBaseUrl

    if (cookie) {
      ctx.options.headers = new Headers(ctx.options.headers)
      ctx.options.headers.set('cookie', cookie)
    }
  })
})
