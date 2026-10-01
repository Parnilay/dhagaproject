# Dhaga & Co: Intelligent Returns Triage Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.10+-E92063.svg?logo=pydantic)](https://docs.pydantic.dev)
[![LangChain LCEL](https://img.shields.io/badge/LangChain-LCEL-1C3C3C.svg)](https://python.langchain.com)
[![uv](https://img.shields.io/badge/uv-Fast%20Python%20Package%20Manager-DE5FE9.svg)](https://github.com/astral-sh/uv)

Automated ingestion, linguistic normalization, and categorical classification of customer returns for **Dhaga & Co**. Transforms messy, code-mixed Hinglish and vernacular free-text entries into structured category intelligence, eliminating the unindexed 44% "Other" vacuum (~₹55 lakh weekly merchandise volume).

---

## 🏗️ Architecture & Project Directory

The project cleanly decouples the **FastAPI Backend** and the **Operational Frontend Dashboard**:

```
dhaga/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app factory, CORS, lifespan
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic-settings BaseSettings
│   │   │   ├── logging.py           # Structured logging
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── triage.py            # Pydantic v2 schemas (ARCHITECTURE.md Section 6)
│   │   │   └── __init__.py
│   │   ├── pipeline/
│   │   │   ├── sanitizer.py         # Phase 0: Deterministic Ingestion & Sanitation (Code)
│   │   │   ├── extractor.py         # Phase 1: Native Linguistic Extraction (Model 1, T=0.0)
│   │   │   ├── router.py            # Phase 2: Programmatic Confidence Gate (Path A, B, C)
│   │   │   ├── evaluator.py         # Phase 3: Dispute Reconciliation (Model 2 Arbiter, T=0.2)
│   │   │   ├── engine.py            # Pipeline Orchestrator (Phase 0 -> Phase 4)
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── supabase_service.py  # Phase 4: Supabase persistence & memory fallback
│   │   │   └── __init__.py
│   │   └── api/
│   │       ├── router.py            # Master API v1 router
│   │       ├── __init__.py
│   │       └── v1/
│   │           └── endpoints/
│   │               ├── health.py    # GET /api/v1/health
│   │               └── triage.py    # POST /triage, GET /triage, GET /analytics/summary
│   ├── scripts/
│   │   ├── supabase_schema.sql      # PostgreSQL schema, enums, indexes, RLS
│   │   └── seed.py                  # 5-minute cold start seeder (Hinglish returns)
│   ├── tests/
│   │   ├── test_api.py              # FastAPI endpoint tests
│   │   ├── test_router.py           # Confidence gate tests (Path A/B/C)
│   │   ├── test_sanitizer.py        # Phase 0 deterministic sanitization tests
│   │   └── test_schemas.py          # Pydantic v2 schema validation tests
│   ├── Dockerfile                   # Production container build
│   └── .env.example
├── frontend/
│   ├── index.html                   # Operational Dashboard + Mobile Intake Simulator
│   ├── css/
│   │   └── style.css                # Polished design system tokens (dark mode, glassmorphism)
│   ├── js/
│   │   ├── app.js                   # State, real-time API integration, audit modal
│   │   └── sample_data.js           # Quick presets (Hinglish, sarcasm, multi-issues)
│   ├── package.json                 # Decoupled frontend scripts
│   └── README.md
├── .env.example                     # Project-level environment template
├── docker-compose.yml               # Container orchestration
├── main.py                          # Convenience dev runner (uv run main.py)
├── pyproject.toml                   # uv project definition & pytest configuration
└── README.md
```

---

## ⚡ 5-Minute Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and SUPABASE credentials (optional for local mock mode)
```

### 2. Run Backend
```bash
# Start FastAPI backend with automatic hot-reloading
uv run uvicorn backend.app.main:app --reload --port 8000
# Alternatively: uv run python main.py
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### 3. Seed Realistic Returns Data
```bash
uv run python backend/scripts/seed.py
```

### 4. Run Decoupled Frontend
```bash
cd frontend
npm run dev
# Or without installing npm dependencies:
# npx -y serve . -l 5173
```
- Open `http://localhost:5173` in your browser.

### 5. Run Unit Tests
```bash
uv run pytest
```

---

## 🔄 End-to-End Pipeline Summary

| Phase | Component | Logic | Model / Engine |
|---|---|---|---|
| **Phase 0** | Ingestion & Sanitation | Strip control chars, regex spam check, character bounds | Deterministic Python |
| **Phase 1** | Native Linguistic Extraction | Standardization without translation drift, dialect detection, sarcasm & multi-issue identification | Model 1 (`gpt-4o-mini`, $T=0.0$) |
| **Phase 2** | Programmatic Confidence Gate | `conf >= 0.85` & no sarcasm $\to$ Path A<br>`conf < 0.85` or sarcasm or conflict $\to$ Path B<br>`conf < 0.40` or low info $\to$ Path C | Deterministic Python |
| **Phase 3** | Dispute Reconciliation | Evaluator-optimizer arbitration for sizing chart conflicts, sarcasm, and vendor defect actionability | Model 2 (`gpt-4o`, $T=0.2$) |
| **Phase 4** | Ingestion & UI State | Persist to Supabase `return_triage_records` and update Category Management dashboard | PostgreSQL / Supabase Client |
