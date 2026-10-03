// Design: Form Field's input (s2kV7R): 38 tall, 0 × 12, radius 9, surface with a border, 14 px, placeholder in
// text-tertiary. Customised: focus is the global focus-ring outline; invalid turns the border danger.
import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"
import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-9.5 w-full min-w-0 rounded-9 border border-border bg-surface px-3 text-14 text-text-primary file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-14 file:font-medium file:text-text-primary placeholder:text-text-tertiary disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-danger",
        className
      )}
      {...props}
    />
  )
}

export { Input }
