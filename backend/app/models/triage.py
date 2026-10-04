from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, computed_field


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
    order_id: str = Field(..., max_length=64, description="Customer order identifier, e.g. ORD-98241")
    sku_id: Optional[str] = Field(default=None, max_length=64, description="Item SKU ID, e.g. DHG-KURTA-042")
    sku: Optional[str] = Field(default=None, max_length=64, description="Alias for sku_id")
    vendor_id: Optional[str] = Field(default=None, max_length=64, description="Vendor identifier, e.g. VND-JAIPUR-01")
    raw_customer_text: Optional[str] = Field(default=None, description="Raw customer return description (Hinglish/English)")
    raw_text: Optional[str] = Field(default=None, description="Alias for raw_customer_text")
    customer_id: Optional[str] = Field(default=None, description="Optional customer account ID")
    catalog_sizing_notes: Optional[str] = Field(
        default=None,
        description="Catalog vendor notes, e.g. 'Slim fit cut, run 1 size small'"
    )

    def get_sku_id(self) -> str:
        return self.sku_id or self.sku or "UNKNOWN-SKU"

    def get_raw_text(self) -> str:
        text = self.raw_customer_text or self.raw_text or ""
        return text.strip()


class SanitationResult(BaseModel):
    is_valid: bool
    sanitized_text: str
    rejection_reason: Optional[str] = None


class ReturnTriageRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    order_id: str = Field(..., max_length=64)
    sku_id: str = Field(..., max_length=64)
    vendor_id: Optional[str] = Field(default=None, max_length=64)
    raw_customer_text: str
    cleaned_customer_text: str
    detected_dialect: Optional[str] = Field(default=None, max_length=32)
    standardized_summary: Optional[str] = None
    primary_category: str = Field(..., max_length=64)
    sub_category: str = Field(..., max_length=64)
    is_multi_issue: bool = False
    is_sarcastic: bool = False
    initial_confidence: float
    final_confidence: float
    status: TriageStatus = TriageStatus.AUTO_TRIAGED
    evaluator_model_invoked: bool = False
    reconciliation_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Computed fields for backward compatibility with frontend/APIs
    @computed_field
    @property
    def sku(self) -> str:
        return self.sku_id

    @computed_field
    @property
    def raw_text(self) -> str:
        return self.raw_customer_text

    @computed_field
    @property
    def sanitized_text(self) -> str:
        return self.cleaned_customer_text

    @computed_field
    @property
    def confidence_score(self) -> float:
        return self.final_confidence

    @computed_field
    @property
    def triage_status(self) -> str:
        return self.status.value

    @computed_field
    @property
    def routing_path(self) -> str:
        if self.evaluator_model_invoked:
            return RoutingPath.PATH_B.value
        elif self.status == TriageStatus.AUTO_TRIAGED:
            return RoutingPath.PATH_A.value
        return RoutingPath.PATH_C.value


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
