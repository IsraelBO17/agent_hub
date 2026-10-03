import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Check, Copy, Icon } from '@/components/ui/icon'

/** Design: the catalog error's "Copy error details" (Jchi9): what failed, for a bug report. */
export function CopyErrorButton({ details }: { details: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => { void navigator.clipboard.writeText(details).then(() => { setCopied(true) }) }
  return (
    <Button variant="secondary" onClick={copy}>
      <Icon icon={copied ? Check : Copy} />
      {copied ? 'Copied' : 'Copy error details'}
    </Button>
  )
}
