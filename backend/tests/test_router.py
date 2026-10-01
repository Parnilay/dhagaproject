import pytest
from backend.app.models.triage import (
    InitialTriageExtraction,
    ReturnCategory,
    RoutingPath,
    TriageStatus,
)
from backend.app.pipeline.router import ProgrammaticConfidenceRouter


def test_routing_path_a_direct():
    extraction = InitialTriageExtraction(
        standardized_english_summary="Garment is too tight in chest area.",
        detected_dialect="Hinglish",
        primary_category=ReturnCategory.FIT_AND_SIZING,
        sub_category="chest_tight",
        is_multi_issue=False,
        is_sarcastic=False,
        confidence_score=0.92
    )
    path = ProgrammaticConfidenceRouter.evaluate(extraction)
    assert path == RoutingPath.PATH_A
    assert ProgrammaticConfidenceRouter.get_initial_status(path) == TriageStatus.AUTO_TRIAGED


def test_routing_path_b_sarcasm():
    extraction = InitialTriageExtraction(
        standardized_english_summary="Sarcastic complaint regarding low quality fabric.",
        detected_dialect="Hinglish",
        primary_category=ReturnCategory.FABRIC_QUALITY,
        sub_category="poor_durability",
        is_multi_issue=False,
        is_sarcastic=True,  # triggers arbiter
        confidence_score=0.95
    )
    path = ProgrammaticConfidenceRouter.evaluate(extraction)
    assert path == RoutingPath.PATH_B


def test_routing_path_b_multi_issue():
    extraction = InitialTriageExtraction(
        standardized_english_summary="Customer reports tight sleeves and torn stitching.",
        detected_dialect="Hinglish",
        primary_category=ReturnCategory.DEFECT_OR_DAMAGE,
        sub_category="stitching_torn",
        is_multi_issue=True,  # triggers arbiter
        is_sarcastic=False,
        confidence_score=0.90
    )
    path = ProgrammaticConfidenceRouter.evaluate(extraction)
    assert path == RoutingPath.PATH_B


def test_routing_path_b_medium_confidence():
    extraction = InitialTriageExtraction(
        standardized_english_summary="Customer unsure about shade difference.",
        detected_dialect="English",
        primary_category=ReturnCategory.COLOR_MISMATCH,
        sub_category="shade_different",
        is_multi_issue=False,
        is_sarcastic=False,
        confidence_score=0.75  # below 0.85
    )
    path = ProgrammaticConfidenceRouter.evaluate(extraction)
    assert path == RoutingPath.PATH_B


def test_routing_path_c_low_confidence():
    extraction = InitialTriageExtraction(
        standardized_english_summary="Unclear statement.",
        detected_dialect="Hinglish",
        primary_category=ReturnCategory.UNCERTAIN_OTHER,
        sub_category="unspecified",
        is_multi_issue=False,
        is_sarcastic=False,
        confidence_score=0.30  # below 0.40 -> immediate bypass to manual review
    )
    path = ProgrammaticConfidenceRouter.evaluate(extraction)
    assert path == RoutingPath.PATH_C
    assert ProgrammaticConfidenceRouter.get_initial_status(path) == TriageStatus.FLAGGED_FOR_MANUAL_REVIEW
