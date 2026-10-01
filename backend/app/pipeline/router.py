from ..core.config import settings
from ..models.triage import (
    InitialTriageExtraction,
    RoutingPath,
    TriageStatus,
)


class ProgrammaticConfidenceRouter:
    """
    Phase 2: Programmatic Confidence Routing Gate (Strictly Deterministic Python)
    Evaluates extraction confidence, sarcasm, and conflict signals to route the payload.
    """

    @classmethod
    def evaluate(cls, extraction: InitialTriageExtraction) -> RoutingPath:
        # Path C: Immediate Rejection / Manual Flagging
        # If extraction confidence is severely low (< 0.40), bypass Model 2 to prevent hallucination
        if extraction.confidence_score < settings.CONFIDENCE_REJECTION_THRESHOLD:
            return RoutingPath.PATH_C

        # Path B: Escalation to Model 2 (Evaluator & Ambiguity Arbiter)
        # Triggered if confidence is mediocre (< 0.85), sarcasm is detected, or multiple conflicting issues exist
        if (
            extraction.confidence_score < settings.CONFIDENCE_DIRECT_THRESHOLD
            or extraction.is_sarcastic
            or extraction.is_multi_issue
        ):
            return RoutingPath.PATH_B

        # Path A: Direct Persistence (Auto Triaged)
        return RoutingPath.PATH_A

    @classmethod
    def get_initial_status(cls, routing_path: RoutingPath) -> TriageStatus:
        if routing_path == RoutingPath.PATH_A:
            return TriageStatus.AUTO_TRIAGED
        elif routing_path == RoutingPath.PATH_C:
            return TriageStatus.FLAGGED_FOR_MANUAL_REVIEW
        return TriageStatus.RECONCILED
