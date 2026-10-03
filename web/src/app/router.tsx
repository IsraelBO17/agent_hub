// The one route table (standard §9; PRODUCT_PLAN §5). Every screen is lazy; route files only re-export a screen.
// RequireAuth guards every screen but sign-in and the shared session (issue #6). HubLayout: the App Header, no
// desktop sidebar. WorkspaceLayout: the sidebar. The shared session has no shell.
import { createBrowserRouter } from 'react-router'
import { RequireAuth } from '@/modules/auth'
import { HubLayout, RootError, RootLayout, WorkspaceLayout } from '@/modules/shell'

export const router = createBrowserRouter([
  {
    Component: RootLayout,
    ErrorBoundary: RootError,
    children: [
      { path: 'sign-in', lazy: () => import('@/app/routes/sign-in') },
      { path: 's/:shareId', lazy: () => import('@/app/routes/shared-session') },
      {
        Component: RequireAuth,
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
        ],
      },
    ],
  },
])
