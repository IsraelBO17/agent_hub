// One layout for empty, error, not-found and no-access views (standard §15). Screens pass the error's
// description (`describeError` in service/); this component knows no domain.
// Design: Empty State (HUrKd): a 560 px card, a 48 px icon tile, title 20/600, body 14, actions below.
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { AlertCircle, FileText, Icon, Lock, RotateCw, SearchX } from '@/components/ui/icon'

type Props =
  | { kind: 'empty'; title: string; description?: string; action?: ReactNode }
  | { kind: 'error'; title?: string; message: string; requestId?: string; retryable?: boolean; onRetry?: () => void; action?: ReactNode }
  | { kind: 'not-found'; title: string; description?: string; action?: ReactNode }
  | { kind: 'no-access'; reason: string }

const icons = { empty: FileText, error: AlertCircle, 'not-found': SearchX, 'no-access': Lock }

export function EmptyState(props: Props) {
  const title = props.kind === 'error' ? (props.title ?? 'Something went wrong') : props.kind === 'no-access' ? "You don't have access" : props.title
  const body = props.kind === 'error' ? props.message : props.kind === 'no-access' ? props.reason : props.description
  return (
    <section role={props.kind === 'error' ? 'alert' : undefined} className="mx-auto flex w-full max-w-140 flex-col items-center gap-3.5 rounded-14 border bg-bg p-8 text-center">
      <span className="flex size-12 items-center justify-center rounded-14 bg-surface-muted">
        <Icon icon={icons[props.kind]} size="md" className="text-text-secondary" />
      </span>
      <h2 className="text-20 font-semibold text-text-primary">{title}</h2>
      {body ? <p className="max-w-95 text-14 leading-relaxed text-text-secondary">{body}</p> : null}
      {props.kind === 'error' && props.requestId ? <p className="text-12 text-text-tertiary">Reference: {props.requestId}</p> : null}
      {props.kind === 'error' && ((props.onRetry && props.retryable !== false) || props.action) ? (
        <div className="flex flex-wrap justify-center gap-2.5 pt-1.5">
          {props.onRetry && props.retryable !== false ? <Button onClick={props.onRetry}><Icon icon={RotateCw} />Try again</Button> : null}
          {props.action}
        </div>
      ) : null}
      {(props.kind === 'empty' || props.kind === 'not-found') && props.action ? <div className="flex gap-2.5 pt-1.5">{props.action}</div> : null}
    </section>
  )
}
