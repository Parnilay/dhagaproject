import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..core.config import settings
from ..core.logging import logger
from ..models.triage import InitialTriageExtraction, ReturnCategory


SYSTEM_PROMPT = """You are Model 1 (Bulk Triage & Extraction Engine) for Dhaga & Co, an Indian fashion and apparel e-commerce brand.
Your job is to read raw customer return explanations (frequently written in code-mixed Hinglish, vernacular Hindi, or colloquial Indian English) and standardize them into clean, structured intelligence.

Taxonomy of ReturnCategory:
- FIT_AND_SIZING: Issues regarding garment dimensions (tight chest, short sleeves, loose waist, incorrect size chart).
- FABRIC_QUALITY: Issues regarding the cloth material (transparent/sheer, rough, cheap polyester feel, shrinks after wash, itchy).
- COLOR_MISMATCH: Discrepancy between catalog photo and received garment (different shade, faded, looks royal blue online but purple in real life).
- DEFECT_OR_DAMAGE: Manufacturing or physical defect (torn stitching, broken zipper, missing buttons, stain, uneven hem).
- LOGISTICS_AND_PACKAGING: Delivery delay, torn outer bag, wrong item inside package.
- BUYER_REGRET: Ordered by mistake, changed mind, found cheaper elsewhere, no longer need for the event.
- UNCERTAIN_OTHER: Pure ambiguity, insufficient detail, or unclassifiable text.

Key Ground Rules:
1. Native Comprehension: Understand code-mixed Hinglish expressions natively (e.g., "kapda bohot halka hai" -> sheer/poor fabric, "chhati pe fas raha hai" -> chest too tight).
2. Avoid Translation Drift: Directly extract English intent while preserving nuanced vernacular complaints.
3. Sarcasm Detection: Identify sarcastic praise (e.g. "Wah kya kapda diya hai, 2 din me hi fatega" -> is_sarcastic=True).
4. Multi-issue Detection: If customer reports two or more distinct complaints (e.g., late delivery AND tight fitting), set is_multi_issue=True.
5. Confidence Scoring: Assign an honest extraction confidence score between 0.00 and 1.00.
"""

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Order ID: {order_id}\nItem SKU: {sku}\nVendor ID: {vendor_id}\nCustomer Return Feedback:\n{raw_text}")
])


class BulkExtractor:
    """
    Phase 1: Native Linguistic Extraction & Standardization (Model 1, T = 0.0)
    Runs via LangChain with Pydantic v2 structured output.
    """

    def __init__(self):
        self.chain = None
        if settings.OPENAI_API_KEY:
            try:
                llm = ChatOpenAI(
                    model=settings.MODEL_1_NAME,
                    temperature=settings.MODEL_1_TEMPERATURE,
                    api_key=settings.OPENAI_API_KEY
                )
                self.chain = EXTRACTION_PROMPT | llm.with_structured_output(InitialTriageExtraction)
                logger.info(f"Model 1 ({settings.MODEL_1_NAME}) initialized with structured output.")
            except Exception as e:
                logger.error(f"Failed to initialize Model 1 LLM: {e}")

    async def extract(self, order_id: str, sku: str, vendor_id: str, text: str) -> InitialTriageExtraction:
        if self.chain:
            try:
                return await self.chain.ainvoke({
                    "order_id": order_id,
                    "sku": sku,
                    "vendor_id": vendor_id,
                    "raw_text": text
                })
            except Exception as e:
                logger.error(f"Model 1 extraction failed: {e}. Falling back to heuristic extractor.")

        # Heuristic fallback for offline / mock testing or when API key is unconfigured
        return self._heuristic_fallback(text)

    def _heuristic_fallback(self, text: str) -> InitialTriageExtraction:
        lower = text.lower()
        
        # Dialect detection
        is_hinglish = bool(re.search(r"\b(hai|tha|thi|kya|bohot|bilkul|kapda|par|aaya|mujhe|nahi|wali|wala|bhai)\b", lower))
        detected_dialect = "Hinglish" if is_hinglish else "English"

        # Sarcasm check
        is_sarcastic = "wah kya" in lower or "badhiya" in lower and ("fatega" in lower or "bekar" in lower)

        # Multi-issue check
        issue_count = 0
        if any(w in lower for w in ["tight", "fitting", "chhoti", "size", "chest"]):
            issue_count += 1
        if any(w in lower for w in ["stitching", "torn", "fata", "defect", "silai"]):
            issue_count += 1
        if any(w in lower for w in ["delivery", "late", "deri", "delay"]):
            issue_count += 1
        is_multi_issue = issue_count >= 2

        # Category mapping
        if "color" in lower or "shade" in lower or "blue" in lower or "faded" in lower or "rang" in lower:
            return InitialTriageExtraction(
                standardized_english_summary="Customer reports garment color/shade does not match catalog image.",
                detected_dialect=detected_dialect,
                primary_category=ReturnCategory.COLOR_MISMATCH,
                sub_category="faded_color_mismatch",
                is_multi_issue=is_multi_issue,
                is_sarcastic=is_sarcastic,
                confidence_score=0.91
            )
        elif "tight" in lower or "fitting" in lower or "size" in lower or "chhoti" in lower or "chest" in lower:
            # If multiple issues (e.g. tight + stitching), confidence is lowered to trigger arbitration
            conf = 0.72 if is_multi_issue else 0.88
            return InitialTriageExtraction(
                standardized_english_summary="Customer reports sizing and fitting defect with sleeves or chest tightness.",
                detected_dialect=detected_dialect,
                primary_category=ReturnCategory.FIT_AND_SIZING,
                sub_category="chest_tight_sizing",
                is_multi_issue=is_multi_issue,
                is_sarcastic=is_sarcastic,
                confidence_score=conf
            )
        elif "transparent" in lower or "sheer" in lower or "kapda" in lower or "quality" in lower or "patla" in lower:
            return InitialTriageExtraction(
                standardized_english_summary="Customer reports fabric is sheer and low quality.",
                detected_dialect=detected_dialect,
                primary_category=ReturnCategory.FABRIC_QUALITY,
                sub_category="transparent_sheer_fabric",
                is_multi_issue=is_multi_issue,
                is_sarcastic=is_sarcastic,
                confidence_score=0.89
            )
        elif "stitching" in lower or "torn" in lower or "fata" in lower or "silai" in lower:
            return InitialTriageExtraction(
                standardized_english_summary="Customer reports torn stitching or physical garment damage.",
                detected_dialect=detected_dialect,
                primary_category=ReturnCategory.DEFECT_OR_DAMAGE,
                sub_category="stitching_torn",
                is_multi_issue=is_multi_issue,
                is_sarcastic=is_sarcastic,
                confidence_score=0.93
            )
        elif "late" in lower or "delivery" in lower or "delay" in lower:
            return InitialTriageExtraction(
                standardized_english_summary="Customer reports severe delivery delay beyond scheduled timeline.",
                detected_dialect=detected_dialect,
                primary_category=ReturnCategory.LOGISTICS_AND_PACKAGING,
                sub_category="logistics_delay",
                is_multi_issue=is_multi_issue,
                is_sarcastic=is_sarcastic,
                confidence_score=0.86
            )
        else:
            return InitialTriageExtraction(
                standardized_english_summary="Unclear or ambiguous return complaint requiring human verification.",
                detected_dialect=detected_dialect,
                primary_category=ReturnCategory.UNCERTAIN_OTHER,
                sub_category="unspecified_return_reason",
                is_multi_issue=is_multi_issue,
                is_sarcastic=is_sarcastic,
                confidence_score=0.35
            )


extractor = BulkExtractor()
