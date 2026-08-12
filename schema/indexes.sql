-- ============================================================
-- Stack Overflow Survey Analytics
-- Step 4: Fact Table Indexes
-- ============================================================

-- Index on country foreign key
CREATE INDEX IF NOT EXISTS idx_fact_responses_country_id
    ON fact_responses(country_id);

-- Index on employment foreign key
CREATE INDEX IF NOT EXISTS idx_fact_responses_employment_id
    ON fact_responses(employment_id);

-- Index on developer type foreign key
CREATE INDEX IF NOT EXISTS idx_fact_responses_dev_type_id
    ON fact_responses(dev_type_id);

-- Index on yearly converted compensation
CREATE INDEX IF NOT EXISTS idx_fact_responses_converted_comp_yearly
    ON fact_responses(converted_comp_yearly);