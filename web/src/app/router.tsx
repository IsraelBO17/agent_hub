// The one route table (standard §9). Every screen is lazy; route files only re-export a screen.
import { createBrowserRouter } from 'react-router'
import { RootError, RootLayout } from '@/modules/shell'

export const router = createBrowserRouter([
  {
    Component: RootLayout,
    ErrorBoundary: RootError,
    children: [
      { index: true, lazy: () => import('@/app/routes/catalog') },
      { path: '*', lazy: () => import('@/app/routes/not-found') },
    ],
  },
])
