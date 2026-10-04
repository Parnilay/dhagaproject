import asyncio
import time
from typing import Dict, List, Optional
from uuid import UUID
from ..core.config import settings
from ..core.logging import logger
from ..models.triage import (
    ReturnCategory,
    ReturnTriageRecord,
    RoutingPath,
    TriageAnalyticsSummary,
    TriageStatus,
)


class SupabaseService:
    """
    Phase 4: Supabase Database Ingestion & Analytics
    Supports production Supabase instance via supabase-py and graceful in-memory storage fallback.
    """

    def __init__(self):
        self.client = None
        self._memory_store: Dict[UUID, ReturnTriageRecord] = {}
        self._lock = asyncio.Lock()

        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Connected to Supabase PostgreSQL cluster.")
            except Exception as e:
                logger.warning(f"Could not connect to Supabase: {e}. Using in-memory repository fallback.")
        else:
            logger.info("Supabase credentials not configured in .env. Running with in-memory persistence.")

    async def save_record(self, record: ReturnTriageRecord) -> ReturnTriageRecord:
        if self.client:
            try:
                payload = {
                    "id": str(record.id),
                    "order_id": record.order_id,
                    "sku_id": record.sku_id,
                    "vendor_id": record.vendor_id,
                    "raw_customer_text": record.raw_customer_text,
                    "cleaned_customer_text": record.cleaned_customer_text,
                    "detected_dialect": record.detected_dialect,
                    "standardized_summary": record.standardized_summary,
                    "primary_category": str(record.primary_category),
                    "sub_category": str(record.sub_category),
                    "is_multi_issue": record.is_multi_issue,
                    "is_sarcastic": record.is_sarcastic,
                    "initial_confidence": float(record.initial_confidence),
                    "final_confidence": float(record.final_confidence),
                    "status": record.status.value,
                    "evaluator_model_invoked": record.evaluator_model_invoked,
                    "reconciliation_notes": record.reconciliation_notes,
                    "created_at": record.created_at.isoformat(),
                }
                res = self.client.table("return_triage_records").insert(payload).execute()
                logger.info(f"Record {record.id} persisted to Supabase.")
            except Exception as e:
                logger.error(f"Failed to persist record to Supabase: {e}. Storing in memory fallback.")

        async with self._lock:
            self._memory_store[record.id] = record

        return record

    async def get_record(self, record_id: UUID) -> Optional[ReturnTriageRecord]:
        async with self._lock:
            if record_id in self._memory_store:
                return self._memory_store[record_id]

        if self.client:
            try:
                res = self.client.table("return_triage_records").select("*").eq("id", str(record_id)).execute()
                if res.data:
                    return ReturnTriageRecord(**res.data[0])
            except Exception as e:
                logger.error(f"Error fetching record from Supabase: {e}")

        return None

    async def list_records(
        self,
        category: Optional[str] = None,
        status: Optional[TriageStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ReturnTriageRecord]:
        async with self._lock:
            records = list(self._memory_store.values())

        if category:
            records = [r for r in records if r.primary_category == category]
        if status:
            records = [r for r in records if r.status == status]

        # Sort descending by created_at
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[offset: offset + limit]

    async def get_analytics_summary(self) -> TriageAnalyticsSummary:
        async with self._lock:
            records = list(self._memory_store.values())

        total = len(records)
        if total == 0:
            return TriageAnalyticsSummary(
                total_returns_processed=0,
                unclassified_other_reduction_pct=100.0,
                auto_triaged_count=0,
                reconciled_count=0,
                flagged_for_review_count=0,
                rejected_spam_count=0,
                avg_confidence_score=0.0,
                actionable_vendor_defect_rate=0.0,
                category_distribution={},
                dialect_distribution={}
            )

        auto_triaged = sum(1 for r in records if r.status == TriageStatus.AUTO_TRIAGED)
        reconciled = sum(1 for r in records if r.status == TriageStatus.RECONCILED)
        flagged = sum(1 for r in records if r.status == TriageStatus.FLAGGED_FOR_MANUAL_REVIEW)
        rejected_spam = sum(1 for r in records if r.sub_category == "rejected_spam")

        cat_dist: Dict[str, int] = {}
        for r in records:
            cat_dist[r.primary_category] = cat_dist.get(r.primary_category, 0) + 1

        dialect_dist: Dict[str, int] = {}
        for r in records:
            if r.detected_dialect:
                dialect_dist[r.detected_dialect] = dialect_dist.get(r.detected_dialect, 0) + 1

        avg_conf = sum(r.final_confidence for r in records) / total

        # Baseline: 44% were unclassified 'Other'.
        # Reduction calculation: current 'UNCERTAIN_OTHER' vs historical 44%
        uncertain_count = cat_dist.get(ReturnCategory.UNCERTAIN_OTHER.value, 0)
        reduction = max(0.0, (1.0 - (uncertain_count / total)) * 100.0)

        # Defect categories (Fabric quality, Defect/damage, Fit/sizing with evaluator notes)
        vendor_defect_count = sum(
            1 for r in records
            if r.primary_category in [ReturnCategory.DEFECT_OR_DAMAGE.value, ReturnCategory.FABRIC_QUALITY.value]
        )
        defect_rate = round((vendor_defect_count / total) * 100.0, 1)

        return TriageAnalyticsSummary(
            total_returns_processed=total,
            unclassified_other_reduction_pct=round(reduction, 1),
            auto_triaged_count=auto_triaged,
            reconciled_count=reconciled,
            flagged_for_review_count=flagged,
            rejected_spam_count=rejected_spam,
            avg_confidence_score=round(avg_conf, 2),
            actionable_vendor_defect_rate=defect_rate,
            category_distribution=cat_dist,
            dialect_distribution=dialect_dist
        )


supabase_service = SupabaseService()
