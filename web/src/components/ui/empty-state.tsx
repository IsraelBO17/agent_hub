// One layout for empty, error, not-found and no-access views (standard §15). Screens pass the error's
// description (`describeError` in service/); this component knows no domain.
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { AlertCircle, FileText, Icon, Lock, SearchX } from '@/components/ui/icon'

type Props =
  | { kind: 'empty'; title: string; description?: string; action?: ReactNode }
  | { kind: 'error'; message: string; requestId?: string; retryable?: boolean; onRetry?: () => void }
  | { kind: 'not-found'; title: string; action?: ReactNode }
  | { kind: 'no-access'; reason: string }

const icons = { empty: FileText, error: AlertCircle, 'not-found': SearchX, 'no-access': Lock }

export function EmptyState(props: Props) {
  const title = props.kind === 'error' ? 'Something went wrong' : props.kind === 'no-access' ? "You don't have access" : props.title
  const body = props.kind === 'error' ? props.message : props.kind === 'no-access' ? props.reason : props.kind === 'empty' ? props.description : undefined
  return (
    <section role={props.kind === 'error' ? 'alert' : undefined} className="flex flex-col items-center gap-3 rounded-xl border border-dashed px-6 py-12 text-center">
      <Icon icon={icons[props.kind]} size="lg" className="text-muted-foreground" />
      <h2 className="text-lg font-medium">{title}</h2>
      {body ? <p className="max-w-prose text-sm text-muted-foreground">{body}</p> : null}
      {props.kind === 'error' && props.requestId ? <p className="text-xs text-muted-foreground">Reference: {props.requestId}</p> : null}
      {props.kind === 'error' && props.onRetry && props.retryable !== false ? (
        <Button variant="outline" onClick={props.onRetry}>Try again</Button>
      ) : null}
      {(props.kind === 'empty' || props.kind === 'not-found') && props.action ? props.action : null}
    </section>
  )
}
