-- ============================================================
-- Query 1: Salary Percentile Within Each Country
-- ============================================================

WITH salary_data AS (
    SELECT
        f.response_id,
        c.country,
        f.converted_comp_yearly AS salary,

        PERCENT_RANK() OVER (
            PARTITION BY c.country
            ORDER BY f.converted_comp_yearly
        ) AS percentile

    FROM fact_responses f

    INNER JOIN dim_country c
        ON f.country_id = c.country_id

    WHERE f.converted_comp_yearly IS NOT NULL
)

SELECT
    response_id,
    country,
    salary,
    ROUND((percentile * 100)::numeric, 2) AS percentile
FROM salary_data
ORDER BY country, percentile DESC;