-- ============================================================
-- Stack Overflow Survey Analytics - Star Schema
-- Step 2: Database Schema
-- ============================================================

-- Drop existing tables so the script can be safely re-run
DROP TABLE IF EXISTS fact_responses CASCADE;
DROP TABLE IF EXISTS dim_country CASCADE;
DROP TABLE IF EXISTS dim_employment CASCADE;
DROP TABLE IF EXISTS dim_developer_type CASCADE;


-- ============================================================
-- Dimension: Country
-- ============================================================

CREATE TABLE dim_country (
    country_id SERIAL PRIMARY KEY,
    country VARCHAR(255) NOT NULL UNIQUE
);


-- ============================================================
-- Dimension: Employment
-- ============================================================

CREATE TABLE dim_employment (
    employment_id SERIAL PRIMARY KEY,
    employment_type VARCHAR(255) NOT NULL UNIQUE
);


-- ============================================================
-- Dimension: Developer Type
-- ============================================================

CREATE TABLE dim_developer_type (
    dev_type_id SERIAL PRIMARY KEY,
    developer_type VARCHAR(255) NOT NULL UNIQUE
);


-- ============================================================
-- Fact: Survey Responses
-- ============================================================

CREATE TABLE fact_responses (
    response_id BIGINT PRIMARY KEY,

    -- Foreign keys to dimensions
    country_id INTEGER NOT NULL,
    employment_id INTEGER,
    dev_type_id INTEGER,

    -- Compensation
    converted_comp_yearly NUMERIC(15, 2),

    -- Experience
    years_of_experience NUMERIC(10, 2),

    -- Technologies
    language_worked_with TEXT,
    language_want_to_work_with TEXT,

    -- Optional useful survey attributes
    age VARCHAR(100),
    remote_work VARCHAR(255),
    ed_level VARCHAR(255),
    main_branch VARCHAR(255),

    -- Foreign key constraints
    CONSTRAINT fk_fact_country
        FOREIGN KEY (country_id)
        REFERENCES dim_country(country_id),

    CONSTRAINT fk_fact_employment
        FOREIGN KEY (employment_id)
        REFERENCES dim_employment(employment_id),

    CONSTRAINT fk_fact_developer_type
        FOREIGN KEY (dev_type_id)
        REFERENCES dim_developer_type(dev_type_id)
);


-- ============================================================
-- Basic indexes for foreign keys
-- Additional performance indexes are created in:
-- schema/indexes.sql
-- ============================================================

CREATE INDEX idx_fact_country_id
    ON fact_responses(country_id);

CREATE INDEX idx_fact_employment_id
    ON fact_responses(employment_id);

CREATE INDEX idx_fact_dev_type_id
    ON fact_responses(dev_type_id);


-- ============================================================
-- Verification-friendly comments
-- ============================================================

COMMENT ON TABLE dim_country IS
    'Country dimension for Stack Overflow survey respondents';

COMMENT ON TABLE dim_employment IS
    'Employment type dimension';

COMMENT ON TABLE dim_developer_type IS
    'Developer role/type dimension';

COMMENT ON TABLE fact_responses IS
    'Central fact table containing Stack Overflow survey responses';

COMMENT ON COLUMN fact_responses.converted_comp_yearly IS
    'Yearly compensation converted to a common currency';

COMMENT ON COLUMN fact_responses.years_of_experience IS
    'Professional coding experience in years';

COMMENT ON COLUMN fact_responses.language_worked_with IS
    'Semicolon-delimited technologies/languages worked with';

COMMENT ON COLUMN fact_responses.language_want_to_work_with IS
    'Semicolon-delimited technologies/languages desired';