/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { msw } from 'msw/vite'
import { defineConfig } from 'vite'

// Standard §3, Appendix C1.
export default defineConfig({
  plugins: [react(), tailwindcss(), msw()],
  resolve: { tsconfigPaths: true },
  build: { sourcemap: 'hidden', manifest: true },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    env: { VITE_API_URL: 'http://localhost:4173' }, // the mocks answer on any origin; tests need an absolute URL
    include: ['src/**/*.test.{ts,tsx}', 'scripts/**/*.test.ts'],
    // MSW 3's Node interceptor trips an undici assertion when a test cancels a mocked response body
    // while a read is pending (a stream stall test does exactly that). Node's own fetch against a real
    // server doesn't. Ignore only that error; every other unhandled error still fails the run.
    onUnhandledError: (error) => !(error.message.includes('assert(!this.aborted)') && (error.stack ?? '').includes('undici')),
  },
})
