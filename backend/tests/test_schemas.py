import pytest
from pydantic import ValidationError
from backend.app.models.triage import (
    InitialTriageExtraction,
    EvaluatorReconciliation,
    ReturnCategory,
    TriageInputRequest,
)


def test_initial_triage_extraction_valid():
    obj = InitialTriageExtraction(
        standardized_english_summary="Sleeves too tight for customer.",
        detected_dialect="Hinglish",
        primary_category=ReturnCategory.FIT_AND_SIZING,
        sub_category="sleeves_tight",
        is_multi_issue=False,
        is_sarcastic=False,
        confidence_score=0.91
    )
    assert obj.confidence_score == 0.91
    assert obj.primary_category == ReturnCategory.FIT_AND_SIZING


def test_initial_triage_extraction_invalid_confidence():
    with pytest.raises(ValidationError):
        InitialTriageExtraction(
            standardized_english_summary="Test summary",
            detected_dialect="English",
            primary_category=ReturnCategory.BUYER_REGRET,
            sub_category="changed_mind",
            is_multi_issue=False,
            is_sarcastic=False,
            confidence_score=1.5  # Invalid, must be <= 1.0
        )


def test_evaluator_reconciliation_schema():
    rec = EvaluatorReconciliation(
        final_primary_category=ReturnCategory.DEFECT_OR_DAMAGE,
        final_sub_category="stitching_defect",
        reconciliation_notes="Resolved in favor of physical defect over sizing fit.",
        is_actionable_for_vendor=True,
        final_confidence_score=0.88,
        requires_human_audit=False
    )
    assert rec.is_actionable_for_vendor is True
    assert rec.final_primary_category == ReturnCategory.DEFECT_OR_DAMAGE
