# Dhaga & Co: Decoupled Frontend

This directory contains the decoupled Operational Dashboard & Mobile Return Intake Simulator for the Intelligent Returns Triage Engine.

## Features
- **Operational Category Management Console:** Real-time stream of triaged returns, confidence scores, dialect badges, and category breakdown.
- **KPI Metrics Bar:** Unclassified "Other" reduction %, auto-triaged count, reconciled count, and actionable vendor defect rate.
- **Mobile Intake Simulator:** Customer return interface for testing code-mixed Hinglish phrases, sarcasm, multi-issues, and spam filters.
- **Audit Modal:** Complete phase-by-phase trace (Phase 0 through Phase 4) for every triage decision.

## Running Locally

You can serve the frontend with any static HTTP server or standard Node package:

```bash
# Using npm
npm run dev

# Or with npx directly
npx -y serve . -l 5173
```

Access the frontend at `http://localhost:5173`. Make sure the FastAPI backend is running on `http://localhost:8000`.
