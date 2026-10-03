// A lucide icon chosen by name at runtime (agents name their icon in their descriptor, so the app can't list
// them). Loaded lazily through named-icon.tsx: lucide's name map is about 15 KB. Unknown names show `bot`.
import { DynamicIcon, iconNames, type IconName } from 'lucide-react/dynamic'

const known = new Set<string>(iconNames)

export default function DynamicGlyph({ name, className }: { name: string; className?: string }) {
  return <DynamicIcon name={(known.has(name) ? name : 'bot') as IconName} className={className} aria-hidden />
}
