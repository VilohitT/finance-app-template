# Frontend — Next.js + Tailwind

Static-exported Next.js (App Router) app. In production it's built once and served by the FastAPI backend. In dev it runs on `:3000` and proxies WebSocket / API calls to the backend on `:8000`.

## Local dev

```bash
npm install
npm run dev
```

Visit `http://localhost:3000`. The backend must be running on `:8000` (see `../backend/README.md`).

## Production build

```bash
npm run build
# Outputs to ./out — the Docker image copies this into /app/frontend/out
# and the backend mounts it as the static root.
```
