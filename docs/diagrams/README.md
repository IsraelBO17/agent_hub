# Diagrams

Mermaid sources (`*.mmd`) are the source of truth; each has a rendered PNG next to it. Keep them in sync with `docs/ARCHITECTURE.md`, and re-render after every change:

```bash
npx -y @mermaid-js/mermaid-cli -i docs/diagrams/architecture.mmd -o docs/diagrams/architecture.png -b white -s 2
```

If npx can't download Chrome, point it at a local one with `-p puppeteer.json`, where the file holds `{"executablePath": "<path to chrome>"}`.

| Diagram | Source | Render |
|---|---|---|
| Architecture (step 2) | [architecture.mmd](architecture.mmd) | [architecture.png](architecture.png) |
| Send a message, normal path (step 3) | [send-message.mmd](send-message.mmd) | [send-message.png](send-message.png) |
| Send a message, failure paths (step 3) | [send-message-failures.mmd](send-message-failures.mmd) | [send-message-failures.png](send-message-failures.png) |
| Data model, ER (step 4) | [er.mmd](er.mmd) | [er.png](er.png) |
| Attachments and approvals (alignment review) | [approval-and-upload.mmd](approval-and-upload.mmd) | [approval-and-upload.png](approval-and-upload.png) |

Mermaid treats `;` as a statement break, even inside a message; use commas in diagram text.
