# Fabrient

Fabrient is an engineering workspace that connects CAD, manufacturing checks, simulation, inspection data, and software tooling for physical-product development.

## What it demonstrates

- Next.js and TypeScript application with authenticated API routes
- Python/FastAPI engineering services
- PostgreSQL-backed application data and migrations
- CadQuery / OCCT-based CAD and STEP workflows
- Computer-vision and measurement utilities using OpenCV
- Simulation-to-reality workflows with deterministic validation and ML components
- MCP tooling for exposing engineering operations to software clients
- Unit, integration, MCP, and Playwright acceptance tests

The repository contains both the product interface and the engineering services used by it. The important boundary is that LLM output is not treated as engineering ground truth: deterministic code, validation, and stored evidence are responsible for engineering results.

## Architecture

```text
Browser
  │
  ▼
Next.js application
  │
  ├── auth / API routes
  ├── PostgreSQL
  └── engineering proxy
          │
          ▼
    Python engineering service
          │
          ├── CAD / STEP
          ├── manufacturing checks
          ├── CV / measurement
          ├── simulation / sim-to-real
          └── engineering validation

MCP clients ───────────────► MCP service ─────► engineering service
```

PostgreSQL is the intended canonical application database. Older Supabase compatibility code remains in the repository and should be removed only after its consumers have been verified.

## Local development

### Web application

Requirements: Node.js 22 and npm 10 or newer.

```bash
npm install
npm run dev
```

### Engineering service

Requirements: Python and the dependencies in `engineering/requirements.txt`.

```bash
cd engineering
pip install -r requirements.txt
uvicorn app.composed:app --reload --port 8000
```

Set `NEXT_PUBLIC_ENGINEERING_API` if the engineering service is running somewhere other than `http://localhost:8000`.

### Environment

Copy `.env.example` to `.env` and provide deployment-specific values. Secrets belong in the local environment or hosting provider, never in Git.

## Verification

```bash
npm run lint
npm run build
npm run test:unit
npm run test:e2e
pytest -q tests/mcp
```

The repository also contains broader preflight and integration checks documented in `package.json`.

## Repository structure

- `app/` - Next.js routes and pages
- `components/` - shared UI components
- `lib/` - frontend/backend integration helpers
- `db/` - PostgreSQL migrations
- `engineering/` - Python engineering application and tests
- `services/` - separately deployable engineering and MCP services
- `tests/` - application, MCP, and end-to-end tests
- `apps/mobile/` - Expo mobile client
- `apps/mobile-native/` - native mobile API clients and tests
- `docs/` - engineering and product documentation

## Status

This is an active prototype. Some product areas and deployment integrations are still evolving, and the repository contains legacy compatibility code from earlier architecture iterations.

## License

See `LICENSE` for the repository license.
