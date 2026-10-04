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

        raw_text = request.get_raw_text()
        sku_id = request.get_sku_id()

        # Phase 0: Deterministic Ingestion & Sanitation (Code)
        sanitation = DeterministicSanitizer.sanitize(raw_text)
        if not sanitation.is_valid:
            logger.info(f"Phase 0 rejected input for Order {request.order_id}: {sanitation.rejection_reason}")
            record = ReturnTriageRecord(
                id=record_id,
                order_id=request.order_id,
                sku_id=sku_id,
                vendor_id=request.vendor_id,
                raw_customer_text=raw_text,
                cleaned_customer_text=sanitation.sanitized_text,
                detected_dialect="Unknown",
                standardized_summary=f"Input rejected by Phase 0 filter: {sanitation.rejection_reason}",
                primary_category=ReturnCategory.UNCERTAIN_OTHER.value,
                sub_category="rejected_spam",
                is_multi_issue=False,
                is_sarcastic=False,
                initial_confidence=0.0,
                final_confidence=0.0,
                status=TriageStatus.FLAGGED_FOR_MANUAL_REVIEW,
                evaluator_model_invoked=False,
                reconciliation_notes=sanitation.rejection_reason
            )
            return await supabase_service.save_record(record)

        # Phase 1: Native Linguistic Extraction & Standardization (Model 1)
        extraction: InitialTriageExtraction = await extractor.extract(
            order_id=request.order_id,
            sku=sku_id,
            vendor_id=request.vendor_id or "UNKNOWN-VENDOR",
            text=sanitation.sanitized_text
        )

        # Phase 2: Programmatic Confidence Routing Gate (Code)
        routing_path = ProgrammaticConfidenceRouter.evaluate(extraction)
        logger.info(f"Routing evaluation for Order {request.order_id}: {routing_path.value} (Confidence: {extraction.confidence_score})")

        final_category = extraction.primary_category
        final_sub_category = extraction.sub_category
        final_confidence = extraction.confidence_score
        reconciliation_notes = None
        evaluator_invoked = False
        triage_status = TriageStatus.AUTO_TRIAGED

        # Phase 3: Dispute Reconciliation & Evaluation (Model 2)
        if routing_path == RoutingPath.PATH_B:
            evaluator_invoked = True
            reconciliation = await arbiter.evaluate(
                raw_text=sanitation.sanitized_text,
                extraction=extraction,
                catalog_sizing_notes=request.catalog_sizing_notes or ""
            )
            final_category = reconciliation.final_primary_category
            final_sub_category = reconciliation.final_sub_category
            final_confidence = reconciliation.final_confidence_score
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

        # Phase 4: Database Ingestion & UI State Update (Code)
        category_str = final_category.value if hasattr(final_category, "value") else str(final_category)
        
        record = ReturnTriageRecord(
            id=record_id,
            order_id=request.order_id,
            sku_id=sku_id,
            vendor_id=request.vendor_id,
            raw_customer_text=raw_text,
            cleaned_customer_text=sanitation.sanitized_text,
            detected_dialect=extraction.detected_dialect,
            standardized_summary=extraction.standardized_english_summary,
            primary_category=category_str,
            sub_category=final_sub_category,
            is_multi_issue=extraction.is_multi_issue,
            is_sarcastic=extraction.is_sarcastic,
            initial_confidence=round(extraction.confidence_score, 2),
            final_confidence=round(final_confidence, 2),
            status=triage_status,
            evaluator_model_invoked=evaluator_invoked,
            reconciliation_notes=reconciliation_notes
        )

        return await supabase_service.save_record(record)


engine = TriageEngine()
