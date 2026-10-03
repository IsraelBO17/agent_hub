// Tells the app's other tabs that this one signed out (standard §14). The message carries no secrets.
const name = 'agent-hub-auth'
const signedOut = 'signed-out'

let sender: BroadcastChannel | null = null

export function broadcastSignOut() {
  if (typeof BroadcastChannel === 'undefined') return
  // One long-lived sender: closing a channel right after posting can drop the message.
  sender ??= new BroadcastChannel(name)
  sender.postMessage(signedOut)
}

/** Calls `onSignOut` when another tab signs out; returns the unsubscribe. */
export function listenForSignOut(onSignOut: () => void): () => void {
  if (typeof BroadcastChannel === 'undefined') return () => undefined
  const channel = new BroadcastChannel(name)
  channel.onmessage = (event: MessageEvent) => { if (event.data === signedOut) onSignOut() }
  return () => { channel.close() }
}
