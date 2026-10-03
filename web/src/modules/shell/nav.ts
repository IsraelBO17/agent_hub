import type { NavSection } from '@/components/layout/app-shell'
import { LayoutGrid } from '@/components/ui/icon'

// The app's navigation. Adding a section or item here is the only change the shell needs.
export const navSections: NavSection[] = [{ items: [{ label: 'All agents', to: '/', icon: LayoutGrid, end: true }] }]
