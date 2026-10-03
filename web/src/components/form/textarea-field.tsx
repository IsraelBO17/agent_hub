import { useController, type Control, type FieldPath, type FieldValues } from 'react-hook-form'
import { FormField } from '@/components/form/form-field'
import { Textarea } from '@/components/ui/textarea'

interface Props<T extends FieldValues, TOut extends FieldValues> {
  control: Control<T, unknown, TOut>
  name: FieldPath<T>
  label: string
  hint?: string
  required?: boolean
  rows?: number
}

export function TextareaField<T extends FieldValues, TOut extends FieldValues = T>({ control, name, label, hint, required, rows = 6 }: Props<T, TOut>) {
  const { field, fieldState, formState } = useController({ control, name })
  const error = fieldState.isTouched || formState.isSubmitted ? fieldState.error?.message : undefined
  return (
    <FormField label={label} hint={hint} required={required} error={error}>
      {(a11y) => <Textarea {...a11y} {...field} value={field.value ?? ''} rows={rows} />}
    </FormField>
  )
}
