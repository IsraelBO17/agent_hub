// Design: Inline Error (Sl1FL) and Inline Error / Warning (U4HXP): a reply that failed or didn't finish, or a
// send that was refused. No Retry yet: the API has no retry endpoint (#9).
import { AlertCircle, Icon, TriangleAlert } from '@/components/ui/icon'
import { cn } from '@/lib/utils'

const tones = {
  danger: { box: 'bg-danger-soft', icon: AlertCircle, accent: 'text-danger', body: 'text-danger-strong' },
  warning: { box: 'bg-warning-subtle', icon: TriangleAlert, accent: 'text-warning', body: 'text-warning-strong' },
}

export function InlineError({ tone = 'danger', title, body, reference, className }: { tone?: keyof typeof tones; title: string; body?: string | undefined; reference?: string | null | undefined; className?: string }) {
  const t = tones[tone]
  return (
    <div role="alert" className={cn('flex items-start gap-2.5 rounded-10 px-3.5 py-3', t.box, className)}>
      <Icon icon={t.icon} className={cn('mt-px size-4', t.accent)} />
      <div className="flex min-w-0 flex-col gap-0.5 text-13">
        <p className={cn('font-semibold', t.accent)}>{title}</p>
        {body ? <p className={t.body}>{body}</p> : null}
        {reference ? <p className={cn('text-12', t.body)}>Reference: {reference}</p> : null}
      </div>
    </div>
  )
}
