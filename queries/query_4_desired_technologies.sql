-- ============================================================
-- Query 4: Most Desired Technologies for Python Developers
-- ============================================================

WITH python_developers AS (
    SELECT
        f.response_id,
        f.language_want_to_work_with
    FROM fact_responses f
    WHERE f.language_worked_with IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM unnest(
              string_to_array(
                  f.language_worked_with,
                  ';'
              )
          ) AS current_language
          WHERE TRIM(current_language) = 'Python'
      )
),

desired_technologies AS (
    SELECT
        TRIM(desired_language) AS technology,
        COUNT(*) AS desired_count
    FROM python_developers p
    CROSS JOIN LATERAL unnest(
        string_to_array(
            p.language_want_to_work_with,
            ';'
        )
    ) AS desired_language
    WHERE p.language_want_to_work_with IS NOT NULL
      AND TRIM(desired_language) <> ''
    GROUP BY
        TRIM(desired_language)
),

ranked_technologies AS (
    SELECT
        technology,
        desired_count,

        ROW_NUMBER() OVER (
            ORDER BY desired_count DESC, technology
        ) AS technology_rank

    FROM desired_technologies
)

SELECT
    technology,
    desired_count,
    technology_rank
FROM ranked_technologies
WHERE technology_rank <= 3
ORDER BY technology_rank;