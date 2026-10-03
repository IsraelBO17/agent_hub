// Google Identity Services (D8, WEB_PROFILE Identity): loads Google's script once and renders its own
// "Continue with Google" button, whose callback gets the ID token the API exchanges. Only the parts used here
// are typed. The CSP allows the script, its frame and its styles from accounts.google.com/gsi.

interface CredentialResponse { credential: string }
interface GoogleId {
  initialize(config: {
    client_id: string
    callback: (response: CredentialResponse) => void
    ux_mode?: 'popup' | 'redirect'
    auto_select?: boolean
    use_fedcm_for_button?: boolean
    itp_support?: boolean
  }): void
  renderButton(parent: HTMLElement, options: {
    type?: 'standard' | 'icon'
    theme?: 'outline' | 'filled_blue' | 'filled_black'
    size?: 'large' | 'medium' | 'small'
    text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
    shape?: 'rectangular' | 'pill' | 'circle' | 'square'
    logo_alignment?: 'left' | 'center'
    width?: number
  }): void
  disableAutoSelect(): void
}
declare global {
  interface Window { google?: { accounts: { id: GoogleId } } }
}

const src = 'https://accounts.google.com/gsi/client'
let loading: Promise<GoogleId> | null = null

/** Loads the script once; rejects if it can't load (offline, blocked). */
export function loadGoogleIdentity(): Promise<GoogleId> {
  loading ??= new Promise<GoogleId>((resolve, reject) => {
    if (window.google) { resolve(window.google.accounts.id); return }
    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.onload = () => { if (window.google) resolve(window.google.accounts.id); else reject(new Error('Google Identity Services did not load')) }
    script.onerror = () => { loading = null; reject(new Error('Google Identity Services did not load')) }
    document.head.append(script)
  })
  return loading
}

/** Renders Google's button into `parent`; `onCredential` gets the ID token after the user picks an account. */
export async function renderGoogleButton(parent: HTMLElement, clientId: string, width: number, onCredential: (idToken: string) => void) {
  const id = await loadGoogleIdentity()
  id.initialize({ client_id: clientId, callback: (r) => { onCredential(r.credential) }, ux_mode: 'popup', auto_select: false, use_fedcm_for_button: true, itp_support: true })
  id.renderButton(parent, { type: 'standard', theme: 'outline', size: 'large', text: 'continue_with', shape: 'rectangular', logo_alignment: 'center', width })
}

/** After sign-out or "Use a different account": Google asks which account instead of reusing the last one. */
export function forgetGoogleAccount() {
  window.google?.accounts.id.disableAutoSelect()
}
