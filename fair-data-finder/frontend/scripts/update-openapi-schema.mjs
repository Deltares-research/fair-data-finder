/**
 * Refreshes openapi/api.json from a running backend.
 *
 * nuxt-open-fetch generates the typed API client from the committed schema, so
 * the image build needs neither network access nor a backend URL. Run this
 * whenever the backend API changes and commit the result.
 *
 *   npm run schema:update
 *   API_URL=http://backend:8000 npm run schema:update
 */
import { writeFile } from 'node:fs/promises'

const base = process.env.API_URL ?? 'http://localhost:8000'
const url = `${ base }/api/api`

const response = await fetch(url)

if (!response.ok) {
  console.error(`Failed to fetch ${ url }: ${ response.status } ${ response.statusText }`)
  process.exit(1)
}

const schema = await response.json()
const target = new URL('../openapi/api.json', import.meta.url)

await writeFile(target, `${ JSON.stringify(schema, null, 2) }\n`)

console.log(`Updated openapi/api.json from ${ url } (${ Object.keys(schema.paths).length } paths)`)
