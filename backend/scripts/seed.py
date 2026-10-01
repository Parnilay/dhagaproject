import asyncio
import os
import sys

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.models.triage import TriageInputRequest
from backend.app.pipeline.engine import engine
from backend.app.services.supabase_service import supabase_service


SAMPLE_RETURNS = [
    {
        "order_id": "ORD-2026-901",
        "sku": "DHG-KURTA-ROYAL-L",
        "vendor_id": "VND-JAIPUR-TEXTILES",
        "raw_text": "Color picture me royal blue dikh raha tha par jab aaya to bilkul faded light blue hai. Photoshoot filter laga rakha hai kya?",
        "catalog_sizing_notes": "Standard A-line cotton kurta, royal blue pigment dye."
    },
    {
        "order_id": "ORD-2026-902",
        "sku": "DHG-SHIRT-LINEN-M",
        "vendor_id": "VND-SURAT-WEAVERS",
        "raw_text": "Bhai sleeves bohot tight hai aur chest pe fitting bilkul kharab hai, aur upar se armpit ki stitching bhi nikli hui thi.",
        "catalog_sizing_notes": "Tailored slim fit linen shirt. Armhole tailored fit."
    },
    {
        "order_id": "ORD-2026-903",
        "sku": "DHG-SAREE-CHANDERI",
        "vendor_id": "VND-VARANASI-SILKS",
        "raw_text": "Wah kya kapda diya hai, 2 din me hi fatega... badhiya Dhaga & Co aisi quality bhejte raho!",
        "catalog_sizing_notes": "Handloom Chanderi silk blend."
    },
    {
        "order_id": "ORD-2026-904",
        "sku": "DHG-DRESS-MAXI-S",
        "vendor_id": "VND-TIRUPUR-KNITS",
        "raw_text": "Kapda bohot transparent aur sheer hai, bina slip ke pehn hi nahi sakte. Bilkul patla material hai.",
        "catalog_sizing_notes": "Lightweight rayon summer dress."
    },
    {
        "order_id": "ORD-2026-905",
        "sku": "DHG-TROUSER-CHINO-32",
        "vendor_id": "VND-DELHI-APPAREL",
        "raw_text": "Size 32 mangwaya tha par 28 jaisa lag raha hai, button band hi nahi ho raha.",
        "catalog_sizing_notes": "Slim taper cut, runs 1 size small according to customer feedback."
    },
    {
        "order_id": "ORD-2026-906",
        "sku": "DHG-ANARKALI-RED-XL",
        "vendor_id": "VND-JAIPUR-TEXTILES",
        "raw_text": "12 din late delivery hui, shaadi ka function nikal gaya ab is suit ka kya karu? Wapas lo jaldi.",
        "catalog_sizing_notes": "Heavy festive embroidery."
    },
    {
        "order_id": "ORD-2026-907",
        "sku": "DHG-DUPATTA-SILK",
        "vendor_id": "VND-VARANASI-SILKS",
        "raw_text": "thik nahi laga",
        "catalog_sizing_notes": "Pure silk dupatta with zari border."
    },
    {
        "order_id": "ORD-2026-908",
        "sku": "DHG-JACKET-DENIM-M",
        "vendor_id": "VND-DELHI-APPAREL",
        "raw_text": "...",
        "catalog_sizing_notes": "Standard denim trucker."
    },
    {
        "order_id": "ORD-2026-909",
        "sku": "DHG-PALAZZO-WHITE",
        "vendor_id": "VND-SURAT-WEAVERS",
        "raw_text": "asdfghjk",
        "catalog_sizing_notes": "Elastic waist flared palazzo."
    }
]


async def seed():
    print("=" * 60)
    print("Dhaga & Co: Intelligent Returns Triage Engine - Cold Start Seeder")
    print("=" * 60)
    print(f"Ingesting {len(SAMPLE_RETURNS)} realistic customer returns requests...\n")

    for idx, item in enumerate(SAMPLE_RETURNS, 1):
        req = TriageInputRequest(
            order_id=item["order_id"],
            sku=item["sku"],
            vendor_id=item["vendor_id"],
            raw_text=item["raw_text"],
            catalog_sizing_notes=item["catalog_sizing_notes"]
        )
        record = await engine.process(req)
        print(f"[{idx}/{len(SAMPLE_RETURNS)}] Order: {record.order_id} | Path: {record.routing_path.value:10} | Status: {record.triage_status.value:26} | Category: {record.primary_category.value:22} | Conf: {record.confidence_score:.2f}")

    print("\n" + "=" * 60)
    analytics = await supabase_service.get_analytics_summary()
    print("Seeding Complete. Ingested Dataset Summary:")
    print(f"- Total Processed: {analytics.total_returns_processed}")
    print(f"- Reduction in Unclassified 'Other': {analytics.unclassified_other_reduction_pct}%")
    print(f"- Auto-Triaged (Path A): {analytics.auto_triaged_count}")
    print(f"- Reconciled via Arbiter (Path B): {analytics.reconciled_count}")
    print(f"- Flagged for Human Review: {analytics.flagged_for_review_count}")
    print(f"- Rejected Spam / Low Quality: {analytics.rejected_spam_count}")
    print(f"- Actionable Vendor Defect Rate: {analytics.actionable_vendor_defect_rate}%")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
