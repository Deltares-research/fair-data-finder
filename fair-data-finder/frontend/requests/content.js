/**
 * Content API requests
 */
/**
 * Fetch markdown content
 * @param {string} path - Path to the markdown file (e.g., 'stars4water/about.md')
 * @returns {Promise<string>} Markdown content as text
 */
export async function fetchMarkdownContent(path) {
  try {
    // $fetch rather than native fetch: this route is served by Nitro itself, and
    // native fetch cannot resolve a relative URL during SSR. Uses /content/
    // instead of /api/content/ to avoid proxy conflicts.
    const content = await $fetch(`/content/${ path }`, {
      responseType: 'text',
    })

    return content
  } catch (error) {
    console.error('Failed to fetch markdown content:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}
