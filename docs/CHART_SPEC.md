# Chart spec

Charts in replies (F22, P1) are rendered from a declarative spec the agent sends. The charts in `design/fleet_dev.pen` ("Rich Reply Content", section 5) are drawn by hand with fixed coordinates: use them for look and feel only, never as geometry to copy (PRODUCT_PLAN §9 item 17).

## Decisions

- **One library: [Recharts](https://recharts.org).** It is React, SVG, declarative, and covers line, area and bar with tooltips and reference lines. No second chart library, and no canvas renderer.
- **One wrapper: `<ChartBlock spec={…} />`.** Agent code and other components never import Recharts directly. The wrapper owns theming, formatting, limits and fallbacks.
- **v1 types: `line` and `bar`.** `line` covers area fills. `bar` covers grouped and stacked. Anything else (pie, scatter, flowchart) is out of scope; the agent should send a table or an image instead.
- **Charts inside HTML artifacts are the agent's own.** They run in the sandboxed iframe and are not covered by this spec.

## The `chart` content block

The agent sends a `chart` block inside a message. The backend validates it against this schema before it reaches the UI.

```ts
type ChartSpec = {
  type: "line" | "bar";
  title: string;                 // "Monthly spending · 2026"
  subtitle?: string;             // "Jan – Sep · all accounts"
  x: {
    key: string;                 // field in each data row
    kind: "category" | "time";   // time values are ISO dates
    label?: string;
  };
  y: {
    label?: string;
    format?: ValueFormat;        // default: { style: "number" }
    min?: number;                // default: nice bound from the data
    max?: number;
  };
  series: Array<{
    key: string;                 // field in each data row
    label: string;               // legend and tooltip label
    color?: "chart-1" | "chart-2" | "chart-3" | "chart-4" | "chart-5" | "chart-6";
  }>;
  data: Array<Record<string, string | number | null>>;
  reference?: Array<{ y: number; label: string }>;   // e.g. a budget line
  stacked?: boolean;             // bar only
  area?: boolean;                // line only: fill under the first series
  caption?: string;              // source or note under the chart
};

type ValueFormat =
  | { style: "number"; compact?: boolean; decimals?: number }
  | { style: "currency"; currency: string; compact?: boolean }  // ISO 4217, e.g. "USD", "NGN"
  | { style: "percent"; decimals?: number };
```

All formatting uses `Intl.NumberFormat` and `Intl.DateTimeFormat` in the viewer's locale.

## Anatomy and tokens

Every colour below is a token in `fleet_dev.pen`. Use the CSS variables generated from those tokens; never use raw hex.

| Part | Rendering | Tokens |
|---|---|---|
| Card | Full width of the message column, radius 12, 1 px border, padding 16. Header: title and subtitle on the left; "Download PNG" and expand buttons on the right. | `surface`, `border` |
| Title / subtitle | 15 / 600 and 13 / regular | `text-primary`, `text-tertiary` |
| Legend | Only with 2 or more series. Above the plot, left aligned: 8 px swatch and a 12 px label. | series colour, `text-secondary` |
| Plot | Height 240 on desktop, 200 below 768 px. | — |
| Series colours | In order: `chart-1` … `chart-6`, unless the spec names one. Maximum 6 series. | `chart-1`–`chart-6` |
| Line | 2 px stroke with round joins. Dots appear only on hover. With `area: true`, the first series gets a fill of its colour at 8% opacity. | series colour |
| Bars | Radius 3 on the top corners. Group gap 8, bar gap 2. Stacked bars have no gap between segments. | series colour |
| Grid | Horizontal lines only, 1 px. | `chart-grid` |
| Axes | No axis lines. Ticks are 12 px labels. X: every category; for time, let Recharts thin the labels. Y: 4–5 nice ticks. | `text-tertiary` |
| Reference line | 1 px dashed, with its label at the right end, 12 px. | `chart-guide`, `text-tertiary` |
| Tooltip | Dark card: radius 8, padding 8–10. First line: the x value (12 px, muted). Then one row per series: swatch, label, value (13 px, 600). If a reference line exists, add its delta ("11% over budget", `chart-4` for over and `chart-2` for under). | `code-header` background, `on-dark`, `on-dark-muted` |
| Hover | A vertical cursor line for line charts; bars get a `hover` band behind the group. | `chart-guide`, `hover` |
| Caption | 12 px under the plot. | `text-tertiary` |

Motion: at most a 150 ms fade on first render. There are no animations while tokens stream in; the chart renders once its block is complete.

## Examples (the two designed charts)

Line chart, "Monthly spending · 2026":

```json
{
  "type": "line",
  "title": "Monthly spending · 2026",
  "subtitle": "Jan – Sep · all accounts",
  "x": { "key": "month", "kind": "category" },
  "y": { "format": { "style": "currency", "currency": "USD", "compact": true }, "min": 2500, "max": 4000 },
  "series": [{ "key": "spending", "label": "Spending" }],
  "reference": [{ "y": 3500, "label": "Budget $3,500" }],
  "area": true,
  "data": [
    { "month": "Jan", "spending": 3050 }, { "month": "Feb", "spending": 2980 },
    { "month": "Mar", "spending": 3210 }, { "month": "Apr", "spending": 3120 },
    { "month": "May", "spending": 3260 }, { "month": "Jun", "spending": 3180 },
    { "month": "Jul", "spending": 3890 }, { "month": "Aug", "spending": 3240 },
    { "month": "Sep", "spending": 3190 }
  ]
}
```

Bar chart, "Spending by category":

```json
{
  "type": "bar",
  "title": "Spending by category",
  "subtitle": "August vs September",
  "x": { "key": "category", "kind": "category" },
  "y": { "format": { "style": "currency", "currency": "USD", "compact": true } },
  "series": [
    { "key": "aug", "label": "August", "color": "chart-2" },
    { "key": "sep", "label": "September", "color": "chart-1" }
  ],
  "data": [
    { "category": "Housing", "aug": 1400, "sep": 1400 },
    { "category": "Groceries", "aug": 540, "sep": 620 },
    { "category": "Dining out", "aug": 310, "sep": 360 },
    { "category": "Transport", "aug": 280, "sep": 260 },
    { "category": "Shopping", "aug": 240, "sep": 210 },
    { "category": "Utilities", "aug": 120, "sep": 118 }
  ]
}
```

The values are illustrative; the design only shows a few of them.

## Limits and fallbacks

| Case | Behaviour |
|---|---|
| Spec fails validation | Render the block as an Inline Error ("This chart couldn't be drawn") with "View data" if `data` is usable. Never render a partial chart. |
| More than 6 series | Reject in the backend validator; the agent must aggregate. |
| More than 500 points | Downsample in the wrapper (LTTB for line; top 20 plus "Other" for bar categories). |
| `null` values | Gaps in lines; missing bars. Never draw them as zero. |
| Empty `data` | "No data for this chart", in the card, 13 px `text-tertiary`. |
| Narrow screens | X labels rotate −30° if they collide; otherwise the chart scrolls horizontally inside its card, never the page. |

## Accessibility

- The SVG has `role="img"` and an `aria-label` made from the title, subtitle, and the series and x range.
- Every chart has a "View data" toggle that renders the same `data` with the table renderer (sticky header, formatted values).
- Series are never distinguished by colour alone: the legend order matches the tooltip order, and line series after the first use a dash pattern.
- Tooltip values are also reachable by keyboard: arrow keys move between x positions when the chart has focus.

## Download

"Download PNG" renders the SVG to a canvas at 2× and saves `<title>.png`. The spec JSON is available through "Copy data" in the message's ⋯ menu.
