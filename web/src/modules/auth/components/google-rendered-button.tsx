// Google's own "Continue with Google" button (Google Identity Services), sized to its container (at most 400 px,
// Google's limit). `onUnavailable` runs when Google's script can't load.
import { useEffect, useRef, useState } from 'react'
import { renderGoogleButton } from '@/lib/google-identity'
import { googleClientId } from '@/service/config'

interface Props { onCredential: (idToken: string) => void; onUnavailable: () => void }

export function GoogleRenderedButton({ onCredential, onUnavailable }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)
  useEffect(() => {
    const el = host.current
    if (!el) return
    renderGoogleButton(el, googleClientId, Math.min(400, Math.round(el.clientWidth) || 360), onCredential)
      .then(() => { setReady(true) })
      .catch(() => { onUnavailable() })
  }, [onCredential, onUnavailable])
  return <div ref={host} aria-busy={!ready} className="flex h-11 w-full items-center justify-center" />
}
