// Build-time configuration (standard §19: only non-secret values). Every key is listed in .env.example.
interface ViteTypeOptions {
  strictImportMetaEnv: unknown
}

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_API_MOCKS?: 'true' | 'false'
  readonly VITE_SENTRY_DSN?: string
  readonly VITE_ENVIRONMENT?: string
  readonly VITE_RELEASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
