import time
from uuid import uuid4
from ..core.config import settings
from ..core.logging import logger
from ..models.triage import (
    InitialTriageExtraction,
    ReturnCategory,
    ReturnTriageRecord,
    RoutingPath,
    TriageInputRequest,
    TriageStatus,
)
from .sanitizer import DeterministicSanitizer
from .extractor import extractor
from .router import ProgrammaticConfidenceRouter
from .evaluator import arbiter
from ..services.supabase_service import supabase_service


class TriageEngine:
    """
    Intelligent Returns Triage Engine Coordinator
    Executes the 5-phase pipeline specified in ARCHITECTURE.md:
    Phase 0: Deterministic Ingestion & Sanitation (Code)
    Phase 1: Native Linguistic Extraction & Standardization (Model 1)
    Phase 2: Programmatic Confidence Routing Gate (Code)
    Phase 3: Dispute Reconciliation & Evaluation (Model 2)
    Phase 4: Database Ingestion & UI State Update (Code)
    """

    async def process(self, request: TriageInputRequest) -> ReturnTriageRecord:
        start_time = time.perf_counter()
        record_id = uuid4()

        # Phase 0: Deterministic Ingestion & Sanitation (Code)
        sanitation = DeterministicSanitizer.sanitize(request.raw_text)
        if not sanitation.is_valid:
            logger.info(f"Phase 0 rejected input for Order {request.order_id}: {sanitation.rejection_reason}")
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            record = ReturnTriageRecord(
                id=record_id,
                order_id=request.order_id,
                sku=request.sku,
                vendor_id=request.vendor_id,
                customer_id=request.customer_id,
                raw_text=request.raw_text,
                sanitized_text=sanitation.sanitized_text,
                detected_dialect="Unknown",
                standardized_summary=f"Input rejected by Phase 0 filter: {sanitation.rejection_reason}",
                primary_category=ReturnCategory.UNCERTAIN_OTHER,
                sub_category="rejected_spam",
                confidence_score=0.0,
                is_multi_issue=False,
                is_sarcastic=False,
                is_actionable_for_vendor=False,
                routing_path=RoutingPath.REJECTED,
                triage_status=TriageStatus.REJECTED_SPAM,
                reconciliation_notes=sanitation.rejection_reason,
                execution_time_ms=round(elapsed_ms, 2)
            )
            return await supabase_service.save_record(record)

        # Phase 1: Native Linguistic Extraction & Standardization (Model 1)
        extraction: InitialTriageExtraction = await extractor.extract(
            order_id=request.order_id,
            sku=request.sku,
            vendor_id=request.vendor_id,
            text=sanitation.sanitized_text
        )

        # Phase 2: Programmatic Confidence Routing Gate (Code)
        routing_path = ProgrammaticConfidenceRouter.evaluate(extraction)
        logger.info(f"Routing evaluation for Order {request.order_id}: {routing_path.value} (Confidence: {extraction.confidence_score})")

        final_category = extraction.primary_category
        final_sub_category = extraction.sub_category
        final_confidence = extraction.confidence_score
        is_actionable = False
        reconciliation_notes = None
        model_2_name = None
        triage_status = TriageStatus.AUTO_TRIAGED

        # Phase 3: Dispute Reconciliation & Evaluation (Model 2)
        if routing_path == RoutingPath.PATH_B:
            model_2_name = settings.MODEL_2_NAME
            reconciliation = await arbiter.evaluate(
                raw_text=sanitation.sanitized_text,
                extraction=extraction,
                catalog_sizing_notes=request.catalog_sizing_notes or ""
            )
            final_category = reconciliation.final_primary_category
            final_sub_category = reconciliation.final_sub_category
            final_confidence = reconciliation.final_confidence_score
            is_actionable = reconciliation.is_actionable_for_vendor
            reconciliation_notes = reconciliation.reconciliation_notes

            if reconciliation.requires_human_audit or final_confidence < 0.50:
                triage_status = TriageStatus.FLAGGED_FOR_MANUAL_REVIEW
            else:
                triage_status = TriageStatus.RECONCILED

        elif routing_path == RoutingPath.PATH_C:
            # Low confidence / ambiguous string bypasses Model 2 to prevent hallucination
            triage_status = TriageStatus.FLAGGED_FOR_MANUAL_REVIEW
            reconciliation_notes = f"Confidence score ({extraction.confidence_score:.2f}) fell below rejection threshold ({settings.CONFIDENCE_REJECTION_THRESHOLD:.2f}). Escalated directly to Category Management human review."
        
        else: # Path A
            triage_status = TriageStatus.AUTO_TRIAGED
            reconciliation_notes = "High confidence extraction directly verified through Path A."

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Phase 4: Database Ingestion & UI State Update (Code)
        record = ReturnTriageRecord(
            id=record_id,
            order_id=request.order_id,
            sku=request.sku,
            vendor_id=request.vendor_id,
            customer_id=request.customer_id,
            raw_text=request.raw_text,
            sanitized_text=sanitation.sanitized_text,
            detected_dialect=extraction.detected_dialect,
            standardized_summary=extraction.standardized_english_summary,
            primary_category=final_category,
            sub_category=final_sub_category,
            confidence_score=final_confidence,
            is_multi_issue=extraction.is_multi_issue,
            is_sarcastic=extraction.is_sarcastic,
            is_actionable_for_vendor=is_actionable,
            routing_path=routing_path,
            triage_status=triage_status,
            reconciliation_notes=reconciliation_notes,
            model_1_model_name=settings.MODEL_1_NAME,
            model_2_model_name=model_2_name,
            execution_time_ms=round(elapsed_ms, 2)
        )

        return await supabase_service.save_record(record)


engine = TriageEngine()
