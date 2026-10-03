import { useState } from 'react'
import { useLocation, useParams } from 'react-router'
import { keepsFocus } from '@/hooks/use-focus-on-navigate'
import { ChatPage } from '@/modules/chat/chat-page'

/**
 * A fresh ChatPage for each conversation, except when a first message gives the new session its URL: that
 * navigation carries `keepFocus`, and the page (with its open stream) stays.
 */
export function ChatRoute() {
  const { agentId = '', sessionId } = useParams()
  const state: unknown = useLocation().state
  const id = `${agentId}/${sessionId ?? ''}`
  const [current, setCurrent] = useState({ id, key: id })
  const key = current.id === id || keepsFocus(state) ? current.key : id
  if (current.id !== id) setCurrent({ id, key })
  return <ChatPage key={key} />
}
