-- ============================================================
-- Query 2: Top 5 Most Worked-With Technologies by Country
-- ============================================================

WITH technology_data AS (
    SELECT
        c.country,
        TRIM(technology) AS technology
    FROM fact_responses f
    INNER JOIN dim_country c
        ON f.country_id = c.country_id
    CROSS JOIN LATERAL unnest(
        string_to_array(
            f.language_worked_with,
            ';'
        )
    ) AS technology
    WHERE f.language_worked_with IS NOT NULL
      AND TRIM(technology) <> ''
),

technology_counts AS (
    SELECT
        country,
        technology,
        COUNT(*) AS usage_count
    FROM technology_data
    GROUP BY
        country,
        technology
),

ranked_technologies AS (
    SELECT
        country,
        technology,
        usage_count,

        ROW_NUMBER() OVER (
            PARTITION BY country
            ORDER BY usage_count DESC, technology
        ) AS technology_rank

    FROM technology_counts
)

SELECT
    country,
    technology,
    usage_count,
    technology_rank
FROM ranked_technologies
WHERE technology_rank <= 5
ORDER BY
    country,
    technology_rank;