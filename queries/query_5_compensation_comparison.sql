-- ============================================================
-- Query 5: Individual Salary vs Average Peer Salary
-- ============================================================

WITH compensation_comparison AS (
    SELECT
        f.response_id,
        c.country,
        dt.developer_type AS dev_type,
        f.converted_comp_yearly AS salary,

        AVG(f.converted_comp_yearly) OVER (
            PARTITION BY c.country, dt.developer_type
        ) AS average_peer_salary

    FROM fact_responses f

    INNER JOIN dim_country c
        ON f.country_id = c.country_id

    INNER JOIN dim_developer_type dt
        ON f.dev_type_id = dt.dev_type_id

    WHERE f.converted_comp_yearly IS NOT NULL
      AND c.country IS NOT NULL
      AND dt.developer_type IS NOT NULL
)

SELECT
    response_id,
    country,
    dev_type,
    ROUND(salary::numeric, 2) AS salary,
    ROUND(average_peer_salary::numeric, 2) AS average_peer_salary,
    ROUND(
        (salary - average_peer_salary)::numeric,
        2
    ) AS difference_from_peer_average
FROM compensation_comparison
ORDER BY country, dev_type, salary DESC;