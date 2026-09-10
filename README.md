# SIH034 — Legal Metrology Compliance Checker

SIH 2026 prototype for checking packaged-commodity label compliance under the Legal Metrology (Packaged Commodities) Rules, 2011.

## Architecture

`Frontend (M5) → FastAPI / Backend (M3) → M1 perception/OCR → M2 compliance rules → M4 PostgreSQL → M3 response → Frontend`

M2 owns legal applicability and compliance decisions. M3 owns orchestration/API. M4 owns persistence. M5 owns the UI. M6 owns domain research and QA.

## Repository layout

```text
SIH034/
├── frontend/                 # M5 — frontend application
├── backend/                  # M3 — backend/API integration
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── integrations/
│   ├── auth/
│   ├── cv/                   # M1
│   ├── ocr/                  # M1
│   ├── extraction/           # M1
│   ├── rules/                # M2
│   ├── compliance/           # M2 integration-facing layer
│   ├── database/             # M4
│   ├── reports/              # M3
│   └── tests/
├── rules-data/               # M2 + M6 legal/rule configuration
├── legal_sources/            # source documents used for rule research
├── research/                 # M6 research and QA material
├── storage/                  # local prototype files; do not commit generated data
├── docs/                     # architecture, API and setup contracts
└── .github/workflows/        # CI
```

## Development

Use feature branches and keep `main` stable. The shared contracts in `docs/` are the integration boundary between modules.

M2 currently runs as a standalone deterministic rules engine with automated tests. M3/M4 integration replaces mocks without changing the compliance semantics.

## Status

The project is being developed as a functional SIH prototype first; production-scale deployment, exhaustive legal coverage and infrastructure hardening are intentionally secondary.
