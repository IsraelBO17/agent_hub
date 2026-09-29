# Diagrams

Mermaid sources (`*.mmd`) are the source of truth; each has a rendered PNG next to it. Keep them in sync with `docs/ARCHITECTURE.md`, and re-render after every change:

```bash
npx -y @mermaid-js/mermaid-cli -i docs/diagrams/architecture.mmd -o docs/diagrams/architecture.png -b white -s 2
```

If npx can't download Chrome, point it at a local one with `-p puppeteer.json`, where the file holds `{"executablePath": "<path to chrome>"}`.

| Diagram | Source | Render |
|---|---|---|
| Architecture (step 2) | [architecture.mmd](architecture.mmd) | [architecture.png](architecture.png) |
