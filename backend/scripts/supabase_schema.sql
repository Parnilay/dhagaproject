-- Supabase Schema for Dhaga & Co: Intelligent Returns Triage Engine
-- Table: return_triage_records

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Enums
DO $$ BEGIN
    CREATE TYPE return_category_enum AS ENUM (
        'FIT_AND_SIZING',
        'FABRIC_QUALITY',
        'COLOR_MISMATCH',
        'DEFECT_OR_DAMAGE',
        'LOGISTICS_AND_PACKAGING',
        'BUYER_REGRET',
        'UNCERTAIN_OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE triage_status_enum AS ENUM (
        'AUTO_TRIAGED',
        'RECONCILED',
        'FLAGGED_FOR_MANUAL_REVIEW',
        'REJECTED_SPAM'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE routing_path_enum AS ENUM (
        'PATH_A',
        'PATH_B',
        'PATH_C',
        'REJECTED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Primary Table
CREATE TABLE IF NOT EXISTS return_triage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    vendor_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100),
    raw_text TEXT NOT NULL,
    sanitized_text TEXT NOT NULL,
    detected_dialect VARCHAR(50),
    standardized_summary TEXT,
    primary_category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(100),
    confidence_score NUMERIC(3, 2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    is_multi_issue BOOLEAN DEFAULT FALSE,
    is_sarcastic BOOLEAN DEFAULT FALSE,
    is_actionable_for_vendor BOOLEAN DEFAULT FALSE,
    routing_path VARCHAR(20) NOT NULL,
    triage_status VARCHAR(50) NOT NULL,
    reconciliation_notes TEXT,
    model_1_model_name VARCHAR(50),
    model_2_model_name VARCHAR(50),
    execution_time_ms NUMERIC(10, 2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. High Performance Indexes for Category Management Queries
CREATE INDEX IF NOT EXISTS idx_triage_primary_category ON return_triage_records (primary_category);
CREATE INDEX IF NOT EXISTS idx_triage_status ON return_triage_records (triage_status);
CREATE INDEX IF NOT EXISTS idx_triage_vendor_id ON return_triage_records (vendor_id);
CREATE INDEX IF NOT EXISTS idx_triage_created_at ON return_triage_records (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_triage_actionable_vendor ON return_triage_records (is_actionable_for_vendor) WHERE is_actionable_for_vendor = TRUE;

-- 4. Enable Row Level Security (RLS)
ALTER TABLE return_triage_records ENABLE ROW LEVEL SECURITY;

-- Allow read access for authenticated and anon users (for dashboard viewing)
CREATE POLICY "Allow public read access" ON return_triage_records
    FOR SELECT USING (true);

-- Allow backend service role / authenticated to insert
CREATE POLICY "Allow insert access" ON return_triage_records
    FOR INSERT WITH CHECK (true);
