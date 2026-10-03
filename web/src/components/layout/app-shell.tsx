// The app shell (standard §8.4): a sidebar that becomes a sheet on mobile, a sticky header, and a
// scrolling content region. Configured by props; screens are its children. Domain-free: modules/shell
// passes the brand and the navigation.
import type { CSSProperties, ReactNode } from 'react'
import { NavItemLink, type NavItem } from '@/components/layout/nav-item-link'
import { SkipLink } from '@/components/layout/skip-link'
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu,
  SidebarProvider, SidebarTrigger,
} from '@/components/ui/sidebar'

export interface NavSection { label?: string; items: NavItem[] }

interface Props {
  brand: ReactNode
  sections: NavSection[]
  header?: ReactNode
  children: ReactNode
}

export function AppShell({ brand, sections, header, children }: Props) {
  return (
    <SidebarProvider style={{ '--sidebar-width': 'var(--layout-sidebar-width)' } as CSSProperties} className="h-dvh">
      <SkipLink />
      <Sidebar collapsible="icon">
        <SidebarHeader className="px-3 py-3">{brand}</SidebarHeader>
        <SidebarContent>
          {sections.map((section, i) => (
            <SidebarGroup key={section.label ?? i}>
              {section.label ? <SidebarGroupLabel>{section.label}</SidebarGroupLabel> : null}
              <SidebarGroupContent>
                <nav aria-label={section.label ?? 'Main'}>
                  <SidebarMenu>{section.items.map((item) => <NavItemLink key={item.to} item={item} />)}</SidebarMenu>
                </nav>
              </SidebarGroupContent>
            </SidebarGroup>
          ))}
        </SidebarContent>
      </Sidebar>
      <SidebarInset className="min-h-0">
        <header className="sticky top-0 z-10 flex h-12 shrink-0 items-center gap-2 border-b bg-background px-3">
          <SidebarTrigger aria-label="Toggle navigation" />
          {header}
        </header>
        <div id="main" tabIndex={-1} className="min-h-0 flex-1 overflow-y-auto outline-none">
          <div className="mx-auto w-full max-w-(--layout-content-width) px-4 py-6 sm:px-6">{children}</div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
