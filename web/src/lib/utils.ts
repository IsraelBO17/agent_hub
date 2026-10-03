// `cn` merges class names (standard §8.2). It is told the design's size names, which it can't know:
// without them a numeric size (13) looks like a colour and is dropped next to a text colour.
import { createCn } from 'cn/config'
import { fontSizes, radii, shadows } from '@/lib/token-names'

export const cn = createCn({ extend: { theme: { text: [...fontSizes], radius: [...radii], shadow: [...shadows] } } })
