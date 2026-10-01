# ARCHITECTURE.md: Intelligent Returns Triage Engine

## 1. System Overview and Core Objective

The Intelligent Returns Triage Engine automates the ingestion, linguistic normalization, and categorical classification of customer return requests for Dhaga & Co. 

Currently, 44% of return requests (~6,547 orders per week) terminate in an unclassified "Other" free-text box, creating an unindexed information vacuum representing ~₹55 lakh in weekly merchandise volume. This system transforms messy, code-mixed Hinglish and vernacular free-text entries into structured, actionable category intelligence stored in Supabase (PostgreSQL) and visualized on an operational dashboard for Category Management.

---

## 2. Core Constraints and Ground Rules

1. **Two Models Minimum:**
   - **Model 1 (Bulk Triage & Extraction):** Lightweight model (`gpt-4o-mini` or `gemini-1.5-flash`) operating at temperature $T = 0.0$ for deterministic extraction and classification.
   - **Model 2 (Evaluator & Ambiguity Arbiter):** Advanced reasoning model (`gpt-4o` or `claude-3-5-sonnet`) operating at temperature $T = 0.2$ for resolving multi-issue conflicts, sarcasm, and catalog size-chart discrepancies.
2. **Deterministic vs. Probabilistic Line:**
   - Input cleaning, regex spam detection, character bounds checking, routing logic, and database persistence are strictly deterministic Python code.
   - Foundation models are invoked exclusively for semantic parsing, Hinglish code-mixed comprehension, sarcasm detection, and root-cause classification.
3. **Structured Outputs:**
   - All model boundaries enforce strict Pydantic v2 schemas (`with_structured_output`). No raw, unstructured markdown or free-text strings pass into backend business logic.
4. **Visible Failure Modes:**
   - Inputs with extraction confidence below 0.50, low-information strings, or unresolvable multi-issue conflicts are visibly tagged as `FLAGGED_FOR_MANUAL_REVIEW` on screen rather than hallucinating an inaccurate classification.
5. **5-Minute Cold Start:**
   - Fully reproducible via standard Python package managers, an environment file (`.env`), and a database migration/seed script.

---

## 3. Technology Stack

- **Backend Framework:** FastAPI (Asynchronous Python 3.11+)
- **LLM Orchestration:** LangChain Expression Language (LCEL) with `RunnableSequence`, `RunnableBranch`, `RunnableLambda`
- **Data Validation & Schemas:** Pydantic v2
- **Database:** Supabase (Managed PostgreSQL) with `supabase-py` / PostgREST
- **Frontend Interface:** 
  - *Option 1 (Unified Monolith):* Mobile-responsive HTML5 / Tailwind CSS served directly by FastAPI.
  - *Option 2 (Decoupled Dashboard):* Streamlit or Gradio hosted on Hugging Face Spaces.
- **Hosting & Deployment:** Render.com / Railway (Backend API) + Supabase Cloud (Database)

---

## 4. End-to-End Execution Pipeline

The processing pipeline executes across five distinct phases:

### Phase 0: Deterministic Ingestion & Sanitation (Code)
- Normalizes whitespace, strips control characters, and evaluates basic input length.
- Rejects empty, single-character, or repetitive spam strings (e.g., "...", "asdf") before invoking model APIs.
- Assigns a unique tracking UUID and captures metadata (Order ID, SKU, Vendor ID, Timestamp).

### Phase 1: Native Linguistic Extraction & Standardization (Model 1)
- Ingests raw Hinglish text directly into Model 1 (Bulk Model, $T = 0.0$) using LCEL.
- Avoids standalone translation drift by performing extraction and standardization in a single prompt chain.
- Maps input into standardized English intent while extracting:
  - Primary Category (e.g., `FIT_AND_SIZING`, `FABRIC_QUALITY`, `COLOR_MISMATCH`, `DEFECT_OR_DAMAGE`, `LOGISTICS_DELAY`)
  - Sub-Category (e.g., `CHEST_TIGHT`, `TRANSPARENT_SHEER`, `WRONG_SHADE`, `STITCHING_TORN`)
  - Detected Input Dialect / Language (e.g., `Hinglish`, `English`, `Devanagari Hindi`)
  - Sarcasm Detected Flag (`True` / `False`)
  - Extraction Confidence Score (`0.00` to `1.00`)

### Phase 2: Programmatic Confidence Routing Gate (Code)
- A deterministic `RunnableBranch` evaluates the output from Phase 1 against programmatic thresholds:
  - **Path A (Direct Persistence):** If `confidence >= 0.85` and `sarcasm_detected == False`, payload routes directly to Supabase.
  - **Path B (Escalation to Evaluator):** If `confidence < 0.85` OR `sarcasm_detected == True` OR multi-category conflict is present, payload routes to Phase 3.
  - **Path C (Immediate Rejection):** If `confidence < 0.40` or text is classified as gibberish, payload bypasses Model 2 and writes directly with status `FLAGGED_FOR_MANUAL_REVIEW`.

### Phase 3: Dispute Reconciliation & Evaluation (Model 2)
- Invokes Model 2 (Advanced Arbiter, $T = 0.2$) via an Evaluator-Optimizer pattern.
- Ingests the original customer text alongside Phase 1 extractions and catalog context (e.g., vendor sizing specifications).
- Resolves conflicts (e.g., customer stating "delivery was late and sleeves are tight" is broken down into primary and secondary root causes).
- Produces a reconciled schema with an updated confidence score and audit explanation.

### Phase 4: Database Ingestion & UI State Update (Code)
- Validates the final payload against the primary persistence schema.
- Writes structured records to the Supabase `return_triage_records` table.
- Broadcasts the result to the frontend operational console with visual state markers.

---

## 5. System Execution Flows

### Primary Ingestion and Routing Flow
- Step 1: Customer submits return explanation via mobile intake.
- Step 2: FastAPI receives payload at `POST /api/v1/triage`.
- Step 3: Python runtime runs deterministic sanity checks.
- Step 4: Model 1 (`gpt-4o-mini`) performs extraction and taxonomy mapping into a Pydantic schema.
- Step 5: Deterministic confidence gate evaluates extracted confidence.
- Step 6a: If confidence is at or above 0.85, system persists to Supabase and marks status as `AUTO_TRIAGED`.
- Step 6b: If confidence is below 0.85 or sarcasm is detected, system escalates to Model 2 (`gpt-4o`).
- Step 7: Model 2 reconciles multi-issue conflicts and vendor metadata.
- Step 8: System persists reconciled output to Supabase with status `RECONCILED` or `FLAGGED_FOR_MANUAL_REVIEW`.
- Step 9: Frontend dashboard reflects real-time analytics for Category Managers.

### Failure Handling Flow
- Input: Unparseable spam or ambiguous text.
- Validation: Schema failure or low confidence caught by code gate.
- Fallback: System writes record with explicit status `FLAGGED_FOR_MANUAL_REVIEW`.
- UI State: Amber/Red warning banner rendered on frontend; silent failure is explicitly prevented.

---

## 6. Detailed Data Schemas

### Pydantic Output Schemas (Model Boundaries)
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ReturnCategory(str, Enum):
    FIT_AND_SIZING = "FIT_AND_SIZING"
    FABRIC_QUALITY = "FABRIC_QUALITY"
    COLOR_MISMATCH = "COLOR_MISMATCH"
    DEFECT_OR_DAMAGE = "DEFECT_OR_DAMAGE"
    LOGISTICS_AND_PACKAGING = "LOGISTICS_AND_PACKAGING"
    BUYER_REGRET = "BUYER_REGRET"
    UNCERTAIN_OTHER = "UNCERTAIN_OTHER"

class InitialTriageExtraction(BaseModel):
    standardized_english_summary: str = Field(
        description="Clean, normalized English summary of the customer's core complaint."
    )
    detected_dialect: str = Field(
        description="Detected dialect or language, e.g., 'Hinglish', 'English', 'Hindi'."
    )
    primary_category: ReturnCategory = Field(
        description="The primary root cause category of the return."
    )
    sub_category: str = Field(
        description="Granular tag, e.g., 'chest_too_tight', 'see_through_fabric', 'color_faded'."
    )
    is_multi_issue: bool = Field(
        description="True if customer reported two or more distinct complaints."
    )
    is_sarcastic: bool = Field(
        description="True if sarcastic tone is identified."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, 
        description="Confidence score between 0.0 and 1.0."
    )

class EvaluatorReconciliation(BaseModel):
    final_primary_category: ReturnCategory
    final_sub_category: str
    reconciliation_notes: str = Field(
        description="Detailed explanation of how ambiguity, sarcasm, or conflicts were resolved."
    )
    is_actionable_for_vendor: bool = Field(
        description="Indicates whether this feedback identifies a concrete vendor/garment defect."
    )
    final_confidence_score: float = Field(ge=0.0, le=1.0)
    requires_human_audit: bool