// Design: the Form Field control (s2kV7R) as a multi-line box (the Feedback Popover's comment box is 84 tall).
// Customised: the input's look; focus is the global focus-ring outline; invalid turns the border danger.
import * as React from "react"
import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-21 w-full rounded-9 border border-border bg-surface px-3 py-2.5 text-14 text-text-primary placeholder:text-text-tertiary disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-danger",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
