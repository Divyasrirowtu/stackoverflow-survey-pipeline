-- ============================================================
-- Query 3: Compensation Ranking Within Years of Experience
-- ============================================================

WITH compensation_data AS (
    SELECT
        f.response_id,
        c.country,
        f.years_of_experience,
        f.converted_comp_yearly AS salary,

        RANK() OVER (
            PARTITION BY f.years_of_experience
            ORDER BY f.converted_comp_yearly DESC
        ) AS compensation_rank

    FROM fact_responses f

    INNER JOIN dim_country c
        ON f.country_id = c.country_id

    WHERE f.converted_comp_yearly IS NOT NULL
      AND f.years_of_experience IS NOT NULL
)

SELECT
    response_id,
    country,
    years_of_experience,
    salary,
    compensation_rank
FROM compensation_data
ORDER BY
    years_of_experience,
    compensation_rank,
    response_id;