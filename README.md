# Stack Overflow Survey Analytics Pipeline

A PostgreSQL-based data engineering and analytics project that loads Stack Overflow Developer Survey data into a star schema and performs analytical queries using SQL window functions.

---

## 1. Project Overview

This project implements an end-to-end analytics pipeline for the Stack Overflow Developer Survey.

The pipeline:

1. Runs PostgreSQL using Docker Compose.
2. Creates a dimensional star schema.
3. Loads Stack Overflow survey data from CSV.
4. Creates indexes to improve query performance.
5. Calculates salary percentiles by country.
6. Finds the top 5 technologies used in different countries.
7. Ranks developers by compensation within experience groups.
8. Finds the most desired technologies among Python developers.
9. Compares individual compensation with peer averages.
10. Generates `EXPLAIN ANALYZE` execution plans for all analytical queries.

---

## 2. Technologies Used

- PostgreSQL
- Docker
- Docker Compose
- Python
- SQL
- PowerShell
- Git/GitHub
- Stack Overflow Developer Survey CSV

---

## 3. Project Structure

```text
stackoverflow-survey-pipeline/
│
├── docker-compose.yml
│
├── data/
│   └── survey_results_public.csv
│
├── schema/
│   ├── schema.sql
│   └── indexes.sql
│
├── scripts/
│   └── load_data.py
│
├── queries/
│   ├── query_1_salary_percentile.sql
│   ├── query_2_top_technologies.sql
│   ├── query_3_compensation_rank.sql
│   ├── query_4_desired_technologies.sql
│   └── query_5_compensation_comparison.sql
│
├── output/
│   ├── query_1_results.csv
│   ├── query_2_results.csv
│   ├── query_3_results.csv
│   ├── query_4_results.csv
│   └── query_5_results.csv
│
├── explain_analyze/
│   ├── query_1_plan.txt
│   ├── query_2_plan.txt
│   ├── query_3_plan.txt
│   ├── query_4_plan.txt
│   └── query_5_plan.txt
│
└── README.md
4. Database Architecture

The project uses a star schema.

Fact Table

fact_responses

This is the central table containing developer survey responses.

It references the dimension tables through foreign keys.

Dimension Tables
dim_country
dim_employment
dim_developer_type

The relationship is:

                    dim_country
                         |
                         |
dim_employment ---- fact_responses ---- dim_developer_type
                         |
                         |
                    Survey Data
5. PostgreSQL Setup

PostgreSQL is run using Docker Compose.

The docker-compose.yml file configures:

PostgreSQL image
Database user
Database password
Database name
Port 5432
PostgreSQL health check

Start PostgreSQL:

docker compose up -d

Check the container:

docker compose ps

The PostgreSQL container should become healthy.

6. Database Schema

The complete database schema is defined in:

schema/schema.sql

It creates:

fact_responses
dim_country
dim_employment
dim_developer_type

The dimension tables use auto-incrementing integer primary keys.

The fact table contains foreign keys referencing the dimension tables.

7. Indexes

Indexes are defined in:

schema/indexes.sql

The following indexes are created on fact_responses:

country_id
employment_id
dev_type_id
converted_comp_yearly

Indexes improve filtering, joins, ranking, and analytical query performance.

8. Source Data

The pipeline expects the official Stack Overflow survey CSV at:

data/survey_results_public.csv

The CSV should contain the survey fields required by the ETL process, including information related to:

Country
Employment
Developer type
Compensation
Years of experience
Languages worked with
Languages desired to work with
9. ETL Process

The ETL script is:

scripts/load_data.py

It performs the following operations:

Connects to PostgreSQL.
Reads the Stack Overflow survey CSV.
Cleans source values.
Handles missing values.
Converts compensation values into numeric values.
Populates dimension tables.
Creates relationships between fact and dimension records.
Loads the fact table.

The script handles invalid or missing compensation values by converting them to NULL where appropriate.

Run the ETL script:

python .\scripts\load_data.py
10. Analytical Queries
Query 1 — Salary Percentile by Country

File:

queries/query_1_salary_percentile.sql

Output:

output/query_1_results.csv

This query calculates each developer's salary percentile within their country.

It uses:

PERCENT_RANK() OVER (
    PARTITION BY country
    ORDER BY salary
)

The result contains:

Response ID
Country
Salary
Percentile
Query 2 — Top 5 Technologies by Country

File:

queries/query_2_top_technologies.sql

Output:

output/query_2_results.csv

This query analyzes semicolon-delimited technology values.

It uses:

string_to_array()
unnest()

to split technologies into individual records.

A window function ranks technologies within each country:

ROW_NUMBER() OVER (
    PARTITION BY country
    ORDER BY usage_count DESC
)

Only the top 5 technologies per country are returned.

Query 3 — Compensation Ranking

File:

queries/query_3_compensation_rank.sql

Output:

output/query_3_results.csv

Developers are ranked by yearly compensation within their years-of-experience group.

The query uses:

RANK() OVER (
    PARTITION BY years_of_experience
    ORDER BY salary DESC
)

This allows developers to be compared with others having the same experience level.

Query 4 — Desired Technologies for Python Developers

File:

queries/query_4_desired_technologies.sql

Output:

output/query_4_results.csv

This query:

Identifies developers who have worked with Python.
Reads the technologies they want to work with.
Splits the semicolon-delimited values.
Counts technology popularity.
Ranks the technologies.
Returns the top 3.

It uses:

string_to_array()
unnest()
ROW_NUMBER()
Query 5 — Compensation Comparison

File:

queries/query_5_compensation_comparison.sql

Output:

output/query_5_results.csv

This query compares each developer's compensation with the average compensation of peers having the same:

Country
Developer type

It uses:

AVG(salary) OVER (
    PARTITION BY country, developer_type
)

The output includes:

Individual salary
Average peer salary
Difference from peer average
11. EXPLAIN ANALYZE

Execution plans for all five analytical queries are stored in:

explain_analyze/

Files:

query_1_plan.txt
query_2_plan.txt
query_3_plan.txt
query_4_plan.txt
query_5_plan.txt

These files contain PostgreSQL EXPLAIN ANALYZE output.

The plans can be used to examine:

Query execution time
Planning time
Sequential scans
Index scans
Sort operations
Hash operations
Window operations
Buffer usage
12. Running EXPLAIN ANALYZE

For example:

@"
EXPLAIN (ANALYZE, BUFFERS)
$(Get-Content ".\queries\query_1_salary_percentile.sql" -Raw)
"@ | docker exec -i stackoverflow-postgres psql -U postgres -d survey_db | Out-File -Encoding utf8 ".\explain_analyze\query_1_plan.txt"

The same approach is used for queries 2 through 5.

13. Database Verification

Check the fact table:

docker exec -it stackoverflow-postgres psql -U postgres -d survey_db -c "SELECT COUNT(*) FROM fact_responses;"

The expected requirement is:

More than 50,000 rows

Check countries:

docker exec -it stackoverflow-postgres psql -U postgres -d survey_db -c "SELECT COUNT(*) FROM dim_country;"

The expected requirement is:

More than 100 rows
14. Verify Tables

Run:

docker exec -it stackoverflow-postgres psql -U postgres -d survey_db -c "\dt"

The database should contain:

fact_responses
dim_country
dim_employment
dim_developer_type
15. Verify Indexes

Run:

docker exec -it stackoverflow-postgres psql -U postgres -d survey_db -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'fact_responses';"

The required indexes should be present.

16. Verify Analytical Outputs

Check all output files:

Get-ChildItem .\output\*.csv

Expected:

query_1_results.csv
query_2_results.csv
query_3_results.csv
query_4_results.csv
query_5_results.csv
17. Verify EXPLAIN ANALYZE Files

Run:

Get-ChildItem .\explain_analyze\*.txt | Select-Object Name,Length

All five files should exist and have a size greater than zero.

18. Complete Project Workflow

The complete workflow is:

Stack Overflow Survey CSV
          |
          v
    Python ETL Script
          |
          v
      PostgreSQL
          |
          v
     Star Schema
          |
          +------------------+
          |                  |
          v                  v
      Fact Table       Dimension Tables
          |
          v
        Indexes
          |
          v
   Analytical SQL Queries
          |
          +---- Query 1: Salary Percentile
          |
          +---- Query 2: Top Technologies
          |
          +---- Query 3: Compensation Rank
          |
          +---- Query 4: Desired Technologies
          |
          +---- Query 5: Peer Comparison
          |
          v
      CSV Outputs
          |
          v
    EXPLAIN ANALYZE
          |
          v
     Query Plans