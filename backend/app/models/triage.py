from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ReturnCategory(str, Enum):
    FIT_AND_SIZING = "FIT_AND_SIZING"
    FABRIC_QUALITY = "FABRIC_QUALITY"
    COLOR_MISMATCH = "COLOR_MISMATCH"
    DEFECT_OR_DAMAGE = "DEFECT_OR_DAMAGE"
    LOGISTICS_AND_PACKAGING = "LOGISTICS_AND_PACKAGING"
    BUYER_REGRET = "BUYER_REGRET"
    UNCERTAIN_OTHER = "UNCERTAIN_OTHER"


class TriageStatus(str, Enum):
    AUTO_TRIAGED = "AUTO_TRIAGED"
    RECONCILED = "RECONCILED"
    FLAGGED_FOR_MANUAL_REVIEW = "FLAGGED_FOR_MANUAL_REVIEW"
    REJECTED_SPAM = "REJECTED_SPAM"


class RoutingPath(str, Enum):
    PATH_A = "PATH_A"  # Direct persistence: confidence >= 0.85 & no sarcasm & single issue
    PATH_B = "PATH_B"  # Escalated to Model 2: confidence < 0.85 OR sarcasm OR multi-issue
    PATH_C = "PATH_C"  # Rejection bypass: confidence < 0.40 or low info -> Flagged
    REJECTED = "REJECTED"  # Phase 0 rejection (spam / bounds)


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
    final_primary_category: ReturnCategory = Field(
        description="Reconciled root cause category."
    )
    final_sub_category: str = Field(
        description="Reconciled granular sub-category tag."
    )
    reconciliation_notes: str = Field(
        description="Detailed explanation of how ambiguity, sarcasm, or conflicts were resolved."
    )
    is_actionable_for_vendor: bool = Field(
        description="Indicates whether this feedback identifies a concrete vendor/garment defect."
    )
    final_confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Updated confidence score after evaluation."
    )
    requires_human_audit: bool = Field(
        description="Flag indicating manual human audit is required."
    )


class TriageInputRequest(BaseModel):
    order_id: str = Field(..., description="Customer order identifier, e.g. ORD-98241")
    sku: str = Field(..., description="Item SKU, e.g. DHG-KURTA-042")
    vendor_id: str = Field(..., description="Vendor identifier, e.g. VND-JAIPUR-01")
    raw_text: str = Field(..., min_length=1, description="Raw customer return description (Hinglish/English)")
    customer_id: Optional[str] = Field(default=None, description="Optional customer account ID")
    catalog_sizing_notes: Optional[str] = Field(
        default=None,
        description="Catalog vendor notes, e.g. 'Slim fit cut, run 1 size small'"
    )


class SanitationResult(BaseModel):
    is_valid: bool
    sanitized_text: str
    rejection_reason: Optional[str] = None


class ReturnTriageRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    order_id: str
    sku: str
    vendor_id: str
    customer_id: Optional[str] = None
    raw_text: str
    sanitized_text: str
    detected_dialect: Optional[str] = None
    standardized_summary: Optional[str] = None
    primary_category: ReturnCategory
    sub_category: Optional[str] = None
    confidence_score: float
    is_multi_issue: bool = False
    is_sarcastic: bool = False
    is_actionable_for_vendor: bool = False
    routing_path: RoutingPath
    triage_status: TriageStatus
    reconciliation_notes: Optional[str] = None
    model_1_model_name: Optional[str] = None
    model_2_model_name: Optional[str] = None
    execution_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TriageAnalyticsSummary(BaseModel):
    total_returns_processed: int
    unclassified_other_reduction_pct: float
    auto_triaged_count: int
    reconciled_count: int
    flagged_for_review_count: int
    rejected_spam_count: int
    avg_confidence_score: float
    actionable_vendor_defect_rate: float
    category_distribution: Dict[str, int]
    dialect_distribution: Dict[str, int]
