// Design: Google Button (hveC0) and Google Button / Loading (Y8uI7x). For real, Google draws its own
// button (Google Identity Services: outline, "Continue with Google"), which is how the browser gets an ID
// token. In mock mode (no Google), a button drawn like the Pencil component sends a fake credential to MSW.
import { Icon, Loader2 } from '@/components/ui/icon'
import { GoogleMark } from '@/modules/auth/components/google-mark'
import { GoogleRenderedButton } from '@/modules/auth/components/google-rendered-button'
import { mocksOn } from '@/service/config'

/** The fake credential mock mode sends; the MSW handler reads the email from it. */
export const mockCredential = 'mock-google-id-token:owner@example.com'

const frame = 'flex h-11 w-full items-center justify-center gap-2.5 rounded-4 border bg-surface px-3 font-google text-14 font-medium'

interface Props { pending: boolean; onCredential: (idToken: string) => void; onUnavailable: () => void }


export function GoogleSignInButton({ pending, onCredential, onUnavailable }: Props) {
  if (pending) {
    return (
      <div role="status" className={`${frame} border-border text-text-tertiary`}>
        <Icon icon={Loader2} className="size-4.5 animate-spin" />
        Signing in…
      </div>
    )
  }
  if (mocksOn) {
    return (
      <button type="button" className={`${frame} border-google-border text-google-text`} onClick={() => { onCredential(mockCredential) }}>
        <GoogleMark className="size-4.5" />
        Continue with Google
      </button>
    )
  }
  return <GoogleRenderedButton onCredential={onCredential} onUnavailable={onUnavailable} />
}
