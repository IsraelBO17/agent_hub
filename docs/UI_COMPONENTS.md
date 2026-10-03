# UI components: Pencil → shadcn/ui on Base UI

| | |
|---|---|
| Status | In use since issue #4 (`web/` exists, tokens generated). Update it as components are built. |
| Date | 2026-10-03 |
| Decision | ARCHITECTURE D28 (shadcn/ui, Base UI implementation, no Radix) |
| Source of truth for looks | [`design/fleet_dev.pen`](../design/fleet_dev.pen); IDs below are from [`design/INDEX.md`](../design/INDEX.md) |

shadcn/ui supplies the structure and the accessible behaviour. The Pencil file decides how everything looks. When the two disagree, restyle the shadcn component; don't change the design. Sizes below come from the Pencil components (padding is vertical × horizontal, in px).

## 1. Setup, when `web/` is created

- **Init:** done by the `web-standard` template (`components.json`, style `base-nova`: shadcn on Base UI). Icons: lucide (shadcn's default, and the design's). After `npx shadcn@latest add`, change the file's `import { cn } from "cn"` to `@/lib/utils` (WEB_PROFILE, Type scale).
- **Folders:** `web/src/components/ui/` holds the generated primitives, restyled in place. `web/src/components/application/` holds the app components that compose them (§3, §4).
- **Add primitives in the issue that first needs them** (`npx shadcn@latest add <name>`), then restyle that file to its Pencil component before it's used.
- **No Radix.** Don't add shadcn `command` (its `cmdk` dependency pulls in `@radix-ui/react-dialog`). `make check` in `web/` fails if `npm ls --all` finds any `@radix-ui` package.
- **Light theme only.** No dark tokens or screens exist (PRODUCT_PLAN §9 item 12): `theme.css` has no `.dark` block, and `.dark` is never set, so the primitives' `dark:` styles never apply.
- **Restyled in #4** (every primitive `web/` has): Button (variants `primary`, `secondary`, `danger`, `ghost`; icon sizes), Tooltip (no arrow), Sidebar (widths), Sheet (scrim), Card (Content Card `l5WJH`), Dialog (with a `DialogBody` part), Confirm Dialog, Form Field (Field, Label, Input, Textarea), Empty State, Page Heading. The rest of §2 is added by the issue that first needs it. Disabled (50 %) and invalid (`danger` border) stand in until those states are drawn (§5 item 2).

### Tokens

A script reads `variables` from `fleet_dev.pen` and writes `web/src/styles/tokens.css` (generated, never edited by hand). The file has variables only for colours and fonts, so sizes, radii and shadows come from `web/design/scale.json`, kept from the values below (WEB_PROFILE, Token pipeline). Every Pencil colour becomes a Tailwind colour under its own name. shadcn's semantic variables then point at those tokens:

| shadcn variable | Pencil token | Note |
|---|---|---|
| `--background` / `--foreground` | `bg` / `text-primary` | |
| `--card`, `--popover` | `surface` | foregrounds `text-primary` |
| `--primary` / `--primary-foreground` | `accent` / `on-accent` | Button / Primary |
| `--secondary` / `--secondary-foreground` | `surface` / `text-primary` | Button / Secondary is surface plus a border |
| `--muted` / `--muted-foreground` | `surface-muted` / `text-tertiary` | |
| `--accent` / `--accent-foreground` | `hover` / `text-primary` | **Name clash:** shadcn's `accent` is the hover fill of menu items. Pencil's `accent` is the brand green and maps to `--primary`. |
| `--destructive` | `danger` | |
| `--border`, `--input` | `border` | Checkbox and radio rings use `control-border` directly |
| `--ring` | `focus-ring` | A 2 px ring with a 2 px offset (gap), drawn with the `Focus Ring` component and shown on the "States · Focus" board. Same value as `accent` |
| `--sidebar`, `--sidebar-accent`, `--sidebar-border` | `sidebar`, `hover`, `border` | |
| `--chart-*` | *unused* | `<ChartBlock>` reads `chart-1`–`6` directly (CHART_SPEC) |

- **Type scale:** reset Tailwind's sizes (`--text-*: initial`) and define only `text-12`, `13`, `14`, `15`, `20`, `28` and `40`, so no other size can be used. `cn` must be told these names (`createCn` from `cn/config`), or it drops `text-13` next to a text colour (WEB_PROFILE, Type scale). Line heights stay with each component (1.35–1.6 in the file). Fonts: `font-ui` Inter and `font-mono` JetBrains Mono; Roboto only inside the Google button.
- **Radii:** reset the scale the same way and define the steps the file uses: `rounded-4`, `5`, `6`, `7`, `8`, `9`, `10`, `12`, `14`, `16` and `rounded-full`. Most controls use 9, cards and callouts 10, menus 12, popovers and toasts 14, dialogs 16.
- **Shadows** (from the components):

| Token | Value | Used by |
|---|---|---|
| `shadow-control` | `0 1px 2px #0000000F` | Segmented Item, Agent Switcher |
| `shadow-raised` | `0 4px 16px #1B1A170D` | Composer |
| `shadow-float` | `0 4px 12px #1B1A171A` | Jump to Latest |
| `shadow-popover` | `0 12px 32px #1B1A171F, 0 1px 3px #1B1A170F` | Menu Panel, Toast, Feedback Popover, Source Preview |
| `shadow-dialog` | `0 24px 60px #1B1A1733, 0 2px 6px #1B1A170F` | Dialog, Confirm Dialog |
| `shadow-palette` | `0 24px 60px #1B1A1740` | Command Palette |

Overlay backdrops use the `scrim`, `scrim-light` and `scrim-strong` tokens, taking the right one for each overlay from its screen.

## 2. Pencil components → shadcn primitives

| Pencil component (ID) | shadcn (Base UI) | Match |
|---|---|---|
| Focus Ring (`Tx1AB`), board "States · Focus" | Each primitive's `focus-visible` style, restyled to this | Every focusable control shows it when focused by keyboard: 2 px `focus-ring`, 2 px gap, radius = the control's radius + 4 (pills stay round). Rows inside menus, the palette and lists (Menu Item, Agent Menu Item, Palette Row, …) take their highlight fill instead (`hover` in menus, `sidebar` in the palette), no ring. |
| Button / Primary, / Secondary, / Danger (`H0OSN`, `XBZK2`, `HsXdL`) | `button`, variants `primary`, `secondary`, `danger` (renamed from shadcn's names) | 8×14, gap 7, 13 px; weight 600 primary and danger, 500 secondary; radius 9 for all three; icon 14. Add a `sm` size (6×12): instances use it in toasts, popovers and banners. |
| Icon Button (`btfe4`) | `button`, sizes `icon` 32, `icon-sm` 30, `icon-xs` 28, `icon-2xs` 24 | Radius 8 (6 at 24), icon 16 `text-secondary`. Always has `aria-label` and a Tooltip. |
| Tooltip (`fkIAs`) | `tooltip` | Fill `text-primary`, text `bg` 12/500, 5×8, radius 6; shortcut in mono `offline`. No arrow (none drawn). |
| Kbd (`rjWo1`) | `kbd` | Height 20, 0×6, radius 5, `surface` + `border`, 12 mono `text-secondary`. |
| Checkbox (`llhcq`) | `checkbox` | 16, radius 4, `control-border`; checked: `accent` fill, 11 px check in `on-accent`. |
| Status Badge (`JQ0rx`), Stage Tag (`nC6tf`) | `badge`, variants `status`, `stage` | Status: `surface-muted` pill, 3×8, dot 7, 12/500. Stage: outlined pill, 2×8. |
| Search Field (`Wjnvx`) | `input-group` + `input` + `kbd` | 240 wide, 8×12, radius 9, icon 15 `text-tertiary`, text 14, ⌘K hint. |
| Form Field (`s2kV7R`) | `field` (label, description, error) + `input` / `input-group` / `select` | Gap 6; label 13/500 `text-secondary`, required `*` in `danger`; control height 38, 0×12, radius 9; helper 12 `text-tertiary`. |
| Select Button (`ZWD7y`) | `select` | Trigger 7×11, radius 9, 13 px, lead icon 14, chevron 13. Popup styled as Menu Panel. |
| Segmented Item (`K1CWuA`) | `toggle-group` (single); `tabs` where it switches panels | Selected item: `surface`, `shadow-control`, radius 7, 6×12, 13/500. Take the track from the screens. |
| Filter Chip (`W0HHV`) | `toggle` | Pill, 6×12, 13/500, count 12 `text-tertiary`, optional dot or 20 px avatar. |
| Reason Chip (`c3s8Su`) | `toggle-group` (multiple) | Pill 6×12, 13 px; selected: `accent-soft` fill, `accent` stroke, check icon. |
| Toggle Row (`sQir5`) | `field` (horizontal) + `switch` | Row 10×12, radius 9; switch 36×20, knob 16, inset 2, on = `accent`. Take the off colour from Settings (`RHrDH`). |
| Choice Option (`CxmKK`) | `radio-group`, card-style items | 420 wide, 11×14, radius 10; round 18 px indicator, selected shows a 12 px check. Question card (F11.7), export options. |
| Menu Panel + Menu Item (`QRlRa`, `koWWb`) | `dropdown-menu`; the same styles for `context-menu` | Panel 220, radius 12, padding 5, gap 1, `shadow-popover`. Item 7×9, radius 6, gap 9, icon 14, label 13, trailing 12 (`Soon` = disabled item). |
| Agent Menu Item (`UauTJ`) | `dropdown-menu` radio item | 288 wide, 7×8, radius 8, avatar, 14/600, status dot 6, check 14 `accent`. |
| Dialog (`dQMxZ`) | `dialog` | 480 wide, radius 16, `shadow-dialog`. Header 18/18/6/22, title 15/600, subtitle 13 (line height 1.5), close Icon Button 30. Body 14/22/18/22, gap 14. Footer `bg` with a top border, 14×22, gap 8. |
| Confirm Dialog (`i3B1e`) | `alert-dialog` | 400 wide, radius 16, `shadow-dialog`, padding 20, gap 14 (a compact layout without the Dialog's header and footer bands). "Delete all" (F9.2) adds an `input` for typing DELETE. |
| Toast (`IjtkQ`) | `toast` (Base UI; not `sonner`) | 380 wide, radius 14, padding 14, gap 12; 32 px round icon on `accent-soft`; title 14/600, body 13; `sm` buttons; close 15. Task complete, deleted with undo (F7.7), approval waiting (`r5Gru`). |
| Feedback Popover (`meKbs`) | `popover` + `textarea` | 380 wide, radius 14, padding 16, gap 14. Comment box 84 tall, radius 10, `bg` fill. |
| Citation Chip + Source Preview (`q3C9LM`, `Ypu1g`) | `hover-card` (Base UI Preview Card) | Chip: height 18, radius 5, `surface-muted`, 12/600 mono. Card: 340 wide, radius 12, padding 14. Must also open from the keyboard and on tap; if Preview Card can't, use `popover`. |
| Panel Tab (`HXUoW`) | `tabs` | Trigger 9×12, gap 6, bordered, icon 13, 12 mono `text-secondary`. |
| Resize Handle (`accqR`) | `resizable` (react-resizable-panels) | 1 px `border` line; grip 9×44 pill, `surface` + `border`. Chat and artifact split about 50/50. |
| Sidebar, Sidebar Nav Item, Session Item, Session Group Label, Sidebar Footer (`hj5RV`, `MoK3u`, `SEJaD`, `rQVuA`, `CpCSr`) | `sidebar` (`--sidebar-width: 284px`) | Nav item 8×10, radius 9, 14/500, icon 16, mono shortcut 12. Session item 8×10, radius 8, 14 `text-secondary`; its `⋯` is a `SidebarMenuAction` that opens a `dropdown-menu`. On mobile the sidebar's own sheet is the sessions drawer (F10.5). If it fights the layout, keep a custom sidebar built from the same parts. |
| Session info drawer (`E3lQz`) | `sheet`, right side | |
| Mobile artifact sheet, attach sheet, agent switcher sheet (`KXQcB`, F11.4 `BXfKu`, F11.10 `wE4kz`) | `drawer` (Base UI, bottom) | |
| Command Palette + Palette Row (`ZHC9i`, `QrHIB`) | `dialog` + Base UI `Autocomplete` (not shadcn `command`, which brings in Radix) | 640 wide, radius 16, `shadow-palette`. Search row 56 tall, 0×18, icon 18, query 15; scope uses a pill Select Button. Group labels 12/600, padding 10/10/4/10. Rows 8×10, radius 9, 28 px lead tile, active row `sidebar` fill. Footer `bg`, 10×16, Kbd hints. The ⌘J quick switch (F8.5) reuses it with agents only. |
| Keyboard shortcuts overlay (`x8PmN9`) | `dialog` + `kbd` | |
| Empty State (`HUrKd`) | `empty` | |
| Callout / Info, / Warning, / Danger, / Success, / Neutral (`TqvAv`, `sGs40`, `S0AYO`, `BGoTk`, `arwhJ`) | `alert`, one variant each | 560, 12×14, radius 10, `*-soft` fill with a `*-line` stroke; icon 17; title 14/600 `*-strong`; body 13 (line height 1.55). In agent replies, remove shadcn's default `role="alert"` so the callout isn't announced. |
| Inline Error (`Sl1FL`), Inline Error / Warning (`U4HXP`), Notice Banner (`D9HsR`) | `alert`, variants `error`, `warning`, `notice` | Inline Error: `danger-soft`, no stroke, title 13/600 `danger`, body `danger-strong`, Retry is a secondary button with a `danger-line` stroke. Notice: `surface-muted`, radius 12, 14×16, icon 18. |
| Tool Call Chip + Tool Call Detail (`Hbhy0`, `pkhri`), Thinking Row (`Fg95V`) | `collapsible` | The chip is the closed trigger and the detail is the open state. Detail header 9×12, radius 10; input and output panes on `bg`. |
| Loading screens (F11.1 `EP1MN`, F11.15 `JgaZ9`) | `skeleton` | |
| Google Button / Loading (`Y8uI7x`), other busy buttons | `spinner` | |
| Separators in Message Actions and the Artifact Toolbar | `separator` | |

## 3. App components built from primitives

| Pencil component (ID) | Built from |
|---|---|
| Composer, Composer / Mobile (`K6k66O`, `OUcXN`) | Auto-growing `textarea`, `button`, Icon Buttons with `tooltip`; the attach menu is a `dropdown-menu` on desktop and a `drawer` on mobile; Attachment Chips in its slot. `shadow-raised`. |
| Attachment Chip, Image Attachment (`xdoWs`, `z1ehKR`) | Custom, with 24 px Icon Buttons for Remove and Retry. The upload ring is an SVG with Base UI Progress for its ARIA. When building, check whether shadcn's new `attachment` component can be restyled to this. |
| User Message, Agent Message (`EfHME`, `BsXl7`) | Custom layout. Message Actions (`SnIqS`) = 28 px Icon Buttons + `tooltip` + `separator`; Version Pager (`FVkS9`) = 24 px Icon Buttons. |
| Message Editor (`x0laEo`) | `textarea` + `button` |
| Agent Switcher (`RZF5q`) | `dropdown-menu` with Agent Menu Items on desktop (F8.2), `drawer` on mobile (F11.10). |
| App Header, Chat Header (`fqLch`, `H0YWK`) | Layout, Icon Buttons, `tooltip`, `dropdown-menu` |
| Artifact Toolbar, Version Row (`AwpSJ`, `Z4Hd3`) | 30 px Icon Buttons + `tooltip`, `separator`. The version button opens a `dropdown-menu` of Version Rows (F3.5). The title becomes an `input` when clicked (F3.6). |
| Approval Card and its variants, Permission Prompt (`m1FtM`, `G4yJz`, `J6Ep4h`, `F2LNrs`, `YwhPJ`) | `card`, `badge`, `button`; the deny reason is a `textarea`; details are a `<dl>` of Detail Rows. |
| Plan Card, Plan Step, Timeline Step (`I05g84`, `aKwZB`, `JGoho`) | Custom ordered lists |
| Agent Card, Library Tile, Artifact Card (and / Generating), Content Card, Tip Card, File Card, Download File, Starter Prompt (`VZuIf`, `JCduD`, `SMBup`, `Apcke`, `l5WJH`, `HFzDp`, `Mr5AY`, `s5qDxc`, `fkUCB`) | `card` + `button`. A clickable card is a single link or button, so it is one tab stop. |
| Recent Session Row, Capability Row, Source Row, Detail Row, Info Row (`V8961f`, `V6Dax`, `q7ISXo`, `wGPRe`, `NEFiE`) | `item`, or plain markup (`<dl>` for Detail and Info rows) |
| Suggestion Pill (`wULfL`), Jump to Latest (`R2yN9`) | `button`, variants `pill` and `float` |
| Message Footer / Stopped, / Still replying, / Still working (`XebGB`, `SjJKc`, `K5UJmM`) | Custom + `button` |
| Session row on mobile (F11.16, F11.17) | `context-menu` for long-press (Base UI opens it on long-press); swipe-to-delete is a custom gesture. |

## 4. Stays custom (no primitive fits)

- **Agent Avatar** (`vCJQN`): an icon tile in the agent's colours, not an image avatar.
- **Status Banner** (`dcn54`): a full-width connection bar with `role="status"`.
- **Stepper** (`sV1X6`): an `<ol>` with `aria-current="step"`.
- **Typing Indicator** (`eFeRx`): announced through a polite live region.
- **Code Block, Inline Code** (`wW1XY`, `Uzd9M`): copying uses an Icon Button with a tooltip.
- **Google Button and / Loading** (`hveC0`, `Y8uI7x`): Google's branding rules set its look (Roboto, height 40, radius 4). Signed in for real, Google draws its own button (Google Identity Services), which is the only way to get an ID token; the drawn one is the mock-mode stand-in, and / Loading is ours (issue #6).
- **`<ChartBlock>`**: Recharts per `CHART_SPEC.md`. Don't add shadcn `chart`.
- **Section Heading, Tile Label** (`o1lqG`, `Vu7nt`): typography helpers.
- **Not built:** Mobile Status Bar, Home Indicator (canvas only).

## 5. Gaps to settle in the design, not in code

1. ~~**No focus state is drawn anywhere.**~~ **Settled 2026-10-03:** a `focus-ring` colour variable (same value as `accent`, used as `--ring`) and a `Focus Ring` component (`Tx1AB`): 2 px ring, 2 px gap, radius = the control's + 4, pills stay round. The "States · Focus" board shows every focusable control focused; rows in menus, the palette and lists use their highlight fill instead of a ring.
2. **Hover, pressed and disabled are drawn only on "Chat Interaction Details"** (`Q6kwA2`). For other controls, decide the state in Pencil first; don't invent it in code.
3. ~~**Button / Danger has radius 8; Primary and Secondary have 9.**~~ **Settled 2026-10-03:** Danger is 9, like Primary and Secondary.
4. ~~**Confirm Dialog differs from Dialog.**~~ **Settled 2026-10-03:** it keeps its compact layout (400 wide, padding 20, gap 14, no header or footer bands) but takes the Dialog's radius 16 and its two shadows (`shadow-dialog`).
5. ~~**Near-duplicate values.**~~ **Settled 2026-10-03:** Agent Switcher uses Segmented Item's shadow (`0 1px 2px #0000000F`), so there is one `shadow-control`. Command Palette keeps its own `shadow-palette`.
6. **Mobile tap targets** must be 44 px (F15), but icon buttons are 24–32 px. Enlarge the hit area on touch, not the drawn size.
