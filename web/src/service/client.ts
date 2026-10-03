// The one API client (standard §11.2). `/add-auth` adds the auth middleware from standard Appendix C4.
import createClient from 'openapi-fetch'
import { apiUrl } from '@/service/config'
import type { paths } from '@/service/generated/schema'

// Look fetch up per request, so MSW and test interceptors apply whatever the import order.
const fetch = (request: Request) => globalThis.fetch(request)

export const api = createClient<paths>({ baseUrl: apiUrl, credentials: 'include', fetch })
