from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from ....models.triage import (
    ReturnCategory,
    ReturnTriageRecord,
    TriageAnalyticsSummary,
    TriageInputRequest,
    TriageStatus,
)
from ....pipeline.engine import engine
from ....services.supabase_service import supabase_service

router = APIRouter()


@router.post(
    "",
    response_model=ReturnTriageRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and Triage Customer Return Request"
)
async def triage_return(request: TriageInputRequest):
    """
    Primary Ingestion and Routing Endpoint (Step 2 in ARCHITECTURE.md)
    - Phase 0: Deterministic sanitation & spam check
    - Phase 1: Model 1 Bulk extraction & standardization (Hinglish/vernacular)
    - Phase 2: Confidence routing gate (Path A, B, or C)
    - Phase 3: Model 2 Dispute reconciliation (if Path B)
    - Phase 4: Supabase persistence & state update
    """
    record = await engine.process(request)
    return record


@router.get(
    "",
    response_model=List[ReturnTriageRecord],
    summary="List Triage Records"
)
async def list_triage_records(
    category: Optional[ReturnCategory] = Query(None, description="Filter by category"),
    status: Optional[TriageStatus] = Query(None, description="Filter by triage status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List returns triage records with status and category filtering for Category Management.
    """
    return await supabase_service.list_records(
        category=category,
        status=status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/analytics/summary",
    response_model=TriageAnalyticsSummary,
    summary="Returns Triage Analytics Summary"
)
async def get_analytics_summary():
    """
    Operational analytics for Category Management:
    - Total returns processed
    - 'Other' box reduction percentage (from 44% baseline)
    - Auto-triaged vs Reconciled vs Flagged counts
    - Actionable vendor defect rate
    - Category & dialect breakdown
    """
    return await supabase_service.get_analytics_summary()


@router.get(
    "/{record_id}",
    response_model=ReturnTriageRecord,
    summary="Get Detailed Triage Record with Audit Trail"
)
async def get_triage_record(record_id: UUID):
    record = await supabase_service.get_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Triage record {record_id} not found"
        )
    return record
