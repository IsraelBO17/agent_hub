// The shell every form field shares (standard §13): label, required mark, hint, and an error shown once
// the field is touched or the form was submitted. The control gets the ids it must reference.
import { useId, type ReactNode } from 'react'
import { Field, FieldDescription, FieldError, FieldLabel } from '@/components/ui/field'

export interface ControlProps {
  id: string
  'aria-invalid': boolean
  'aria-describedby': string | undefined
  'aria-required': boolean | undefined
}

interface Props {
  label: string
  hint?: string | undefined
  required?: boolean | undefined
  error?: string | undefined
  children: (control: ControlProps) => ReactNode
}

export function FormField({ label, hint, required, error, children }: Props) {
  const id = useId()
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ')
  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>
        {label}
        {required ? <span aria-hidden className="text-destructive">*</span> : null}
      </FieldLabel>
      {children({
        id,
        'aria-invalid': Boolean(error),
        'aria-describedby': describedBy === '' ? undefined : describedBy,
        'aria-required': required ? true : undefined,
      })}
      {hint ? <FieldDescription id={hintId}>{hint}</FieldDescription> : null}
      {error ? <FieldError id={errorId}>{error}</FieldError> : null}
    </Field>
  )
}
