import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

// Design: Button / Primary (H0OSN), Button / Secondary (XBZK2), Button / Danger (HsXdL), Icon Button (btfe4).
// Customised (UI_COMPONENTS §2): restyled to the Pencil components; variants renamed primary, secondary,
// danger (shadcn's default, outline, destructive); icon sizes 32, 30, 28 and 24. Focus is the global
// focus-ring outline (globals.css); hover and pressed aren't drawn yet (UI_COMPONENTS §5 item 2), so none
// is styled. 44 px touch targets on coarse pointers by enlarging the hit area (standard §17).
const buttonVariants = cva(
  "relative pointer-coarse:after:absolute pointer-coarse:after:-inset-1.5 pointer-coarse:after:min-h-11 pointer-coarse:after:min-w-11 group/button inline-flex shrink-0 items-center justify-center rounded-9 border border-transparent bg-clip-padding text-13 whitespace-nowrap select-none disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-3.5",
  {
    variants: {
      variant: {
        primary: "bg-accent font-semibold text-on-accent",
        secondary: "border-border bg-surface font-medium text-text-primary",
        danger: "bg-danger font-semibold text-on-accent",
        ghost: "text-text-secondary [&_svg:not([class*='size-'])]:size-4",
        link: "text-accent underline-offset-4 hover:underline",
      },
      size: {
        default: "gap-1.75 px-3.5 py-2",
        sm: "gap-1.5 px-3 py-1.5",
        icon: "size-8 rounded-8",
        "icon-sm": "size-7.5 rounded-8",
        "icon-xs": "size-7 rounded-8",
        "icon-2xs": "size-6 rounded-6",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "primary",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
