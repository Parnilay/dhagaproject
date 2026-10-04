-- Supabase Schema for Dhaga & Co: Intelligent Returns Triage Engine
-- Aligned with production category intelligence specifications

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create triage_status enum type
DO $$ BEGIN
    CREATE TYPE triage_status AS ENUM (
        'AUTO_TRIAGED',
        'RECONCILED',
        'FLAGGED_FOR_MANUAL_REVIEW'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create return_triage_records table
CREATE TABLE IF NOT EXISTS return_triage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(64) NOT NULL,
    sku_id VARCHAR(64) NOT NULL,
    vendor_id VARCHAR(64),
    raw_customer_text TEXT NOT NULL,
    cleaned_customer_text TEXT NOT NULL,
    detected_dialect VARCHAR(32),
    standardized_summary TEXT,
    primary_category VARCHAR(64) NOT NULL,
    sub_category VARCHAR(64) NOT NULL,
    is_multi_issue BOOLEAN DEFAULT FALSE,
    is_sarcastic BOOLEAN DEFAULT FALSE,
    initial_confidence NUMERIC(3,2) NOT NULL,
    final_confidence NUMERIC(3,2) NOT NULL,
    status triage_status NOT NULL DEFAULT 'AUTO_TRIAGED',
    evaluator_model_invoked BOOLEAN DEFAULT FALSE,
    reconciliation_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Indexing for Category Management queries
CREATE INDEX IF NOT EXISTS idx_return_triage_category ON return_triage_records(primary_category);
CREATE INDEX IF NOT EXISTS idx_return_triage_vendor ON return_triage_records(vendor_id);
CREATE INDEX IF NOT EXISTS idx_return_triage_status ON return_triage_records(status);
CREATE INDEX IF NOT EXISTS idx_return_triage_created_at ON return_triage_records(created_at DESC);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE return_triage_records ENABLE ROW LEVEL SECURITY;

-- Allow public / anon read access (for dashboard operational views)
CREATE POLICY "Allow read access to return_triage_records" ON return_triage_records
    FOR SELECT USING (true);

-- Allow authenticated / service role insert access
CREATE POLICY "Allow insert access to return_triage_records" ON return_triage_records
    FOR INSERT WITH CHECK (true);
