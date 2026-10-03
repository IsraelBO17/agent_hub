// The one route table (standard §9; PRODUCT_PLAN §5). Every screen is lazy; route files only re-export a screen.
// HubLayout: the App Header, no desktop sidebar. WorkspaceLayout: the sidebar. The shared session has no shell.
import { createBrowserRouter } from 'react-router'
import { HubLayout, RootError, RootLayout, WorkspaceLayout } from '@/modules/shell'

export const router = createBrowserRouter([
  {
    Component: RootLayout,
    ErrorBoundary: RootError,
    children: [
      {
        Component: HubLayout,
        children: [
          { index: true, lazy: () => import('@/app/routes/catalog') },
          { path: 'agents/:agentId/about', lazy: () => import('@/app/routes/agent-detail') },
          { path: '*', lazy: () => import('@/app/routes/not-found') },
        ],
      },
      {
        Component: WorkspaceLayout,
        children: [
          { path: 'agents/:agentId', lazy: () => import('@/app/routes/new-session') },
          { path: 'agents/:agentId/:sessionId', lazy: () => import('@/app/routes/session') },
          { path: 'artifacts', lazy: () => import('@/app/routes/artifacts') },
          { path: 'archived', lazy: () => import('@/app/routes/archived') },
          { path: 'settings', lazy: () => import('@/app/routes/settings') },
        ],
      },
      { path: 's/:shareId', lazy: () => import('@/app/routes/shared-session') },
    ],
  },
])
