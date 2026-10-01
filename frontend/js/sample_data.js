// Realistic Indian Fashion & Apparel Return Complaints for Dhaga & Co
const SAMPLE_PRESETS = [
  {
    title: "🎨 Royal Blue Mismatch",
    order_id: "ORD-2026-901",
    sku: "DHG-KURTA-ROYAL-L",
    vendor_id: "VND-JAIPUR-TEXTILES",
    raw_text: "Color picture me royal blue dikh raha tha par jab aaya to bilkul faded light blue hai. Photoshoot filter laga rakha hai kya?",
    catalog_sizing_notes: "A-line cotton kurta, royal blue pigment dye."
  },
  {
    title: "👔 Tight Sleeves + Torn Stitching",
    order_id: "ORD-2026-902",
    sku: "DHG-SHIRT-LINEN-M",
    vendor_id: "VND-SURAT-WEAVERS",
    raw_text: "Bhai sleeves bohot tight hai aur chest pe fitting bilkul kharab hai, aur upar se armpit ki stitching bhi nikli hui thi.",
    catalog_sizing_notes: "Tailored slim fit linen shirt. Armhole tailored fit."
  },
  {
    title: "🎭 Sarcastic Praise",
    order_id: "ORD-2026-903",
    sku: "DHG-SAREE-CHANDERI",
    vendor_id: "VND-VARANASI-SILKS",
    raw_text: "Wah kya kapda diya hai, 2 din me hi fatega... badhiya Dhaga & Co aisi quality bhejte raho!",
    catalog_sizing_notes: "Handloom Chanderi silk blend."
  },
  {
    title: "👗 Transparent Sheer Fabric",
    order_id: "ORD-2026-904",
    sku: "DHG-DRESS-MAXI-S",
    vendor_id: "VND-TIRUPUR-KNITS",
    raw_text: "Kapda bohot transparent aur sheer hai, bina slip ke pehn hi nahi sakte. Bilkul patla material hai.",
    catalog_sizing_notes: "Lightweight rayon summer dress."
  },
  {
    title: "📏 Size 32 vs 28",
    order_id: "ORD-2026-905",
    sku: "DHG-TROUSER-CHINO-32",
    vendor_id: "VND-DELHI-APPAREL",
    raw_text: "Size 32 mangwaya tha par 28 jaisa lag raha hai, button band hi nahi ho raha.",
    catalog_sizing_notes: "Slim taper cut, runs 1 size small according to customer feedback."
  },
  {
    title: "🚚 12 Days Delivery Delay",
    order_id: "ORD-2026-906",
    sku: "DHG-ANARKALI-RED-XL",
    vendor_id: "VND-JAIPUR-TEXTILES",
    raw_text: "12 din late delivery hui, shaadi ka function nikal gaya ab is suit ka kya karu? Wapas lo jaldi.",
    catalog_sizing_notes: "Heavy festive embroidery."
  },
  {
    title: "🚫 Spam Filter ('...')",
    order_id: "ORD-2026-908",
    sku: "DHG-JACKET-DENIM-M",
    vendor_id: "VND-DELHI-APPAREL",
    raw_text: "...",
    catalog_sizing_notes: "Standard denim trucker."
  },
  {
    title: "⚠️ Low-Info ('thik nahi laga')",
    order_id: "ORD-2026-907",
    sku: "DHG-DUPATTA-SILK",
    vendor_id: "VND-VARANASI-SILKS",
    raw_text: "thik nahi laga",
    catalog_sizing_notes: "Pure silk dupatta with zari border."
  }
];
