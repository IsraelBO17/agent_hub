import { useController, type Control, type FieldPath, type FieldValues } from 'react-hook-form'
import { FormField } from '@/components/form/form-field'
import { Input } from '@/components/ui/input'

interface Props<T extends FieldValues, TOut extends FieldValues> {
  control: Control<T, unknown, TOut>
  name: FieldPath<T>
  label: string
  hint?: string
  required?: boolean
  type?: 'text' | 'email' | 'url' | 'search' | 'tel' | 'password'
  autoComplete?: string
}

export function TextField<T extends FieldValues, TOut extends FieldValues = T>({ control, name, label, hint, required, type = 'text', autoComplete }: Props<T, TOut>) {
  const { field, fieldState, formState } = useController({ control, name })
  const error = fieldState.isTouched || formState.isSubmitted ? fieldState.error?.message : undefined
  return (
    <FormField label={label} hint={hint} required={required} error={error}>
      {(a11y) => <Input {...a11y} {...field} value={field.value ?? ''} type={type} autoComplete={autoComplete} />}
    </FormField>
  )
}
