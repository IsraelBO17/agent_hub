import { useCallback, useState } from 'react'
import { readDraft, writeDraft } from '@/utils/drafts'

/** The composer's text for one agent's new session or one session, kept as a draft (SPEC: drafts). */
export function useDraft(key: string) {
  const [state, setState] = useState(() => ({ key, text: readDraft(key) }))
  const text = state.key === key ? state.text : readDraft(key)
  const setText = useCallback((next: string) => {
    writeDraft(key, next)
    setState({ key, text: next })
  }, [key])
  return [text, setText] as const
}
