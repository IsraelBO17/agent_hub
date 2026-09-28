# Design

The Agent Hub design lives in [`fleet_dev.pen`](fleet_dev.pen), a [Pencil](https://pencil.dev) canvas. It is the source of truth for the front end's look, components and flows.

| File | What it is |
|---|---|
| `fleet_dev.pen` | The design file. Open it in Pencil to view or edit it. |
| [`INDEX.md`](INDEX.md) | Generated map of the file: variables, components by group (with IDs and slots), reference screens, and the 10 user flows with the trigger for each step. |
| `tools/pen_index.py` | Regenerates `INDEX.md`. Needs only Python 3. |

## Working with the file without Pencil

A `.pen` file is plain JSON, so it can be read and scripted directly:

- `variables`: the design tokens (colours, `font-ui`, `font-mono`). Nodes reference them as `"$token"`, for example `"fill": "$accent"`.
- `children`: top-level frames (222). The 85 with `"reusable": true` are components.
- Nodes use flexbox-like layout fields (`layout`, `gap`, `padding`, `alignItems`, `justifyContent`, `width` / `height`, `fill_container`).
- Instances are `{"type": "ref", "ref": "<component id>"}`. `descendants` overrides properties of nodes inside the instance, keyed by the node ID, or an ID path such as `"xjiXy/Jg8uM"` for nested instances.
- Slots are nodes with a `slot` key. Its value lists the components suggested for that slot.
- Icons are `{"type": "icon", "library": "lucide", "icon": "<name>"}`.

Find a node by searching for its ID from `INDEX.md`, for example `"id": "PBQLh"` for the Catalog screen.

## Canvas layout

| Area | Where (y) |
|---|---|
| Component library, 8 labelled groups | −7,240 to −200 |
| Core screens and interaction boards | 0 to ~5,000 |
| Artifact screens and boards | 5,200 to ~13,000 |
| Sessions screens and board | 13,400 |
| Agent management screens and board | 16,700 |
| User flows (index at x −1,500) | 21,700 to ~36,300 |

## After editing the design

1. Save in Pencil and copy the file over `design/fleet_dev.pen`.
2. Run `python3 design/tools/pen_index.py`.
3. Commit both files together.
