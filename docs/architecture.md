# System Architecture

## Module flow

`M5 Frontend → M3 Backend/API → M1 CV/OCR/Extraction → M2 Rules/Compliance → M4 PostgreSQL → M3 → M5`

M6 provides legal requirements and QA scenarios across the system.

## Ownership

- M1: perception, OCR and information extraction
- M2: legal applicability and compliance decisions
- M3: API, orchestration, integration and reports
- M4: PostgreSQL schema, persistence and retrieval
- M5: frontend/UI
- M6: legal research, requirements and QA

## MVP principle

Use a modular monolith and mock boundaries during parallel development. Do not introduce microservices or Docker as prerequisites.

## Stable contracts

The M1 observation contract and M2 compliance-result contract are shared integration boundaries. Evidence IDs must remain traceable from M1 text blocks through M2 results, M3 responses and M4 persistence.
