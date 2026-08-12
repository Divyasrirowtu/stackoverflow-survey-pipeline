import csv
import os
import sys
from decimal import Decimal, InvalidOperation

import psycopg2
from psycopg2.extras import execute_batch


# ============================================================
# Configuration
# ============================================================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "survey_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

CSV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "survey_results_public.csv",
)


# ============================================================
# Utility functions
# ============================================================

def clean_text(value):
    """Convert empty/whitespace values to None."""
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def parse_decimal(value):
    """
    Convert a numeric value to Decimal.
    Invalid or missing values become None.
    """
    value = clean_text(value)

    if value is None:
        return None

    # Remove common formatting characters.
    value = value.replace(",", "")
    value = value.replace("$", "")

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def parse_years_of_experience(value):
    """
    Convert YearsCode into a numeric number of years.

    Handles:
    - numeric values
    - Less than 1 year
    - More than 50 years
    - invalid values
    """
    value = clean_text(value)

    if value is None:
        return None

    value_lower = value.lower()

    if value_lower in {"less than 1 year", "<1", "< 1"}:
        return Decimal("0.5")

    if value_lower in {"more than 50 years", ">50", "> 50"}:
        return Decimal("50")

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def split_multi_value(value):
    """
    Split Stack Overflow's semicolon-delimited values.

    Example:
        Python;SQL;Java
    becomes:
        ['Python', 'SQL', 'Java']
    """
    value = clean_text(value)

    if value is None:
        return []

    return [
        item.strip()
        for item in value.split(";")
        if item.strip()
    ]


def first_non_empty(row, column_names):
    """Return the first available non-empty column value."""
    for column in column_names:
        if column in row:
            value = clean_text(row[column])

            if value is not None:
                return value

    return None


# ============================================================
# Database connection
# ============================================================

def get_connection():
    print("Connecting to PostgreSQL...")

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    print("PostgreSQL connection successful.")

    return connection


# ============================================================
# CSV column mapping
# ============================================================

def get_column(row, *possible_names):
    """
    Find a column using several possible column names.
    """
    for name in possible_names:
        if name in row:
            return row[name]

    return None


# ============================================================
# Dimension loading
# ============================================================

def load_dimensions(connection, rows):
    print("\nLoading dimension tables...")

    countries = set()
    employments = set()
    developer_types = set()

    for row in rows:
        country = clean_text(
            get_column(row, "Country")
        )

        employment = clean_text(
            get_column(row, "Employment")
        )

        developer_type = clean_text(
            get_column(row, "DevType", "DevTypeName")
        )

        if country:
            countries.add(country)

        if employment:
            employments.add(employment)

        if developer_type:
            developer_types.add(developer_type)

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Country dimension
    # --------------------------------------------------------

    country_data = [
        (country,)
        for country in sorted(countries)
    ]

    execute_batch(
        cursor,
        """
        INSERT INTO dim_country (country)
        VALUES (%s)
        ON CONFLICT (country) DO NOTHING
        """,
        country_data,
        page_size=1000,
    )

    print(f"Countries processed: {len(country_data)}")

    # --------------------------------------------------------
    # Employment dimension
    # --------------------------------------------------------

    employment_data = [
        (employment,)
        for employment in sorted(employments)
    ]

    execute_batch(
        cursor,
        """
        INSERT INTO dim_employment (employment_type)
        VALUES (%s)
        ON CONFLICT (employment_type) DO NOTHING
        """,
        employment_data,
        page_size=1000,
    )

    print(f"Employment types processed: {len(employment_data)}")

    # --------------------------------------------------------
    # Developer type dimension
    # --------------------------------------------------------

    developer_type_data = [
        (developer_type,)
        for developer_type in sorted(developer_types)
    ]

    execute_batch(
        cursor,
        """
        INSERT INTO dim_developer_type (developer_type)
        VALUES (%s)
        ON CONFLICT (developer_type) DO NOTHING
        """,
        developer_type_data,
        page_size=1000,
    )

    print(
        f"Developer types processed: "
        f"{len(developer_type_data)}"
    )

    connection.commit()

    cursor.close()

    print("Dimension tables loaded successfully.")


# ============================================================
# Dimension lookup dictionaries
# ============================================================

def get_dimension_lookups(connection):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT country_id, country
        FROM dim_country
        """
    )

    country_lookup = {
        country: country_id
        for country_id, country in cursor.fetchall()
    }

    cursor.execute(
        """
        SELECT employment_id, employment_type
        FROM dim_employment
        """
    )

    employment_lookup = {
        employment_type: employment_id
        for employment_id, employment_type in cursor.fetchall()
    }

    cursor.execute(
        """
        SELECT dev_type_id, developer_type
        FROM dim_developer_type
        """
    )

    developer_type_lookup = {
        developer_type: dev_type_id
        for dev_type_id, developer_type in cursor.fetchall()
    }

    cursor.close()

    return (
        country_lookup,
        employment_lookup,
        developer_type_lookup,
    )


# ============================================================
# Fact table loading
# ============================================================

def load_fact_table(connection, rows):
    print("\nLoading fact_responses...")

    (
        country_lookup,
        employment_lookup,
        developer_type_lookup,
    ) = get_dimension_lookups(connection)

    fact_rows = []

    skipped_rows = 0

    for row in rows:
        response_id = clean_text(
            get_column(row, "ResponseId", "ResponseID")
        )

        country = clean_text(
            get_column(row, "Country")
        )

        employment = clean_text(
            get_column(row, "Employment")
        )

        developer_type = clean_text(
            get_column(row, "DevType", "DevTypeName")
        )

        if not response_id or not country:
            skipped_rows += 1
            continue

        try:
            response_id_int = int(response_id)
        except (ValueError, TypeError):
            skipped_rows += 1
            continue

        country_id = country_lookup.get(country)

        if country_id is None:
            skipped_rows += 1
            continue

        employment_id = employment_lookup.get(employment)

        developer_type_id = developer_type_lookup.get(
            developer_type
        )

        converted_comp = parse_decimal(
            get_column(
                row,
                "ConvertedCompYearly",
                "ConvertedComp"
            )
        )

        years_experience = parse_years_of_experience(
            get_column(
                row,
                "YearsCode",
                "YearsCodePro",
                "YearsCodeProfessional"
            )
        )

        language_worked_with = clean_text(
            get_column(
                row,
                "LanguageHaveWorkedWith",
                "LanguageWorkedWith"
            )
        )

        language_want_to_work_with = clean_text(
            get_column(
                row,
                "LanguageWantToWorkWith",
                "LanguageWantToWorkWith"
            )
        )

        age = clean_text(
            get_column(row, "Age")
        )

        remote_work = clean_text(
            get_column(
                row,
                "RemoteWork"
            )
        )

        ed_level = clean_text(
            get_column(
                row,
                "EdLevel"
            )
        )

        main_branch = clean_text(
            get_column(
                row,
                "MainBranch"
            )
        )

        fact_rows.append(
            (
                response_id_int,
                country_id,
                employment_id,
                developer_type_id,
                converted_comp,
                years_experience,
                language_worked_with,
                language_want_to_work_with,
                age,
                remote_work,
                ed_level,
                main_branch,
            )
        )

    cursor = connection.cursor()

    insert_sql = """
        INSERT INTO fact_responses (
            response_id,
            country_id,
            employment_id,
            dev_type_id,
            converted_comp_yearly,
            years_of_experience,
            language_worked_with,
            language_want_to_work_with,
            age,
            remote_work,
            ed_level,
            main_branch
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (response_id) DO UPDATE SET
            country_id = EXCLUDED.country_id,
            employment_id = EXCLUDED.employment_id,
            dev_type_id = EXCLUDED.dev_type_id,
            converted_comp_yearly =
                EXCLUDED.converted_comp_yearly,
            years_of_experience =
                EXCLUDED.years_of_experience,
            language_worked_with =
                EXCLUDED.language_worked_with,
            language_want_to_work_with =
                EXCLUDED.language_want_to_work_with,
            age = EXCLUDED.age,
            remote_work = EXCLUDED.remote_work,
            ed_level = EXCLUDED.ed_level,
            main_branch = EXCLUDED.main_branch
    """

    execute_batch(
        cursor,
        insert_sql,
        fact_rows,
        page_size=1000,
    )

    connection.commit()

    cursor.close()

    print(
        f"Fact rows processed: {len(fact_rows)}"
    )

    print(
        f"Rows skipped because of invalid required data: "
        f"{skipped_rows}"
    )


# ============================================================
# Verification
# ============================================================

def verify_data(connection):
    print("\nRunning ETL verification...")

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM dim_country"
    )

    country_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM dim_employment"
    )

    employment_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM dim_developer_type"
    )

    developer_type_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM fact_responses"
    )

    fact_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM fact_responses
        WHERE converted_comp_yearly IS NOT NULL
        """
    )

    compensation_count = cursor.fetchone()[0]

    print("\n========================================")
    print("ETL VERIFICATION")
    print("========================================")

    print(
        f"dim_country:        {country_count:,}"
    )

    print(
        f"dim_employment:     {employment_count:,}"
    )

    print(
        f"dim_developer_type: {developer_type_count:,}"
    )

    print(
        f"fact_responses:     {fact_count:,}"
    )

    print(
        f"Non-null salaries:  {compensation_count:,}"
    )

    print("========================================")

    if country_count > 100:
        print("PASS: More than 100 countries.")
    else:
        print(
            "WARNING: Country count is not greater than 100."
        )

    if fact_count > 50000:
        print("PASS: More than 50,000 fact rows.")
    else:
        print(
            "WARNING: Fact row count is not greater than 50,000."
        )

    cursor.close()


# ============================================================
# Main ETL
# ============================================================

def main():
    print("========================================")
    print("Stack Overflow Survey ETL")
    print("========================================")

    if not os.path.exists(CSV_FILE):
        print(
            f"ERROR: CSV file not found:\n{CSV_FILE}"
        )
        sys.exit(1)

    print(f"CSV file: {CSV_FILE}")

    connection = None

    try:
        connection = get_connection()

        print("\nReading CSV file...")

        with open(
            CSV_FILE,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            rows = list(reader)

        print(
            f"CSV rows read: {len(rows):,}"
        )

        if not rows:
            print("ERROR: CSV file contains no data.")
            sys.exit(1)

        load_dimensions(
            connection,
            rows,
        )

        load_fact_table(
            connection,
            rows,
        )

        verify_data(
            connection
        )

        print("\n========================================")
        print("ETL COMPLETED SUCCESSFULLY")
        print("========================================")

    except psycopg2.Error as error:
        if connection:
            connection.rollback()

        print(
            "\nPostgreSQL error:"
        )
        print(error)

        sys.exit(1)

    except Exception as error:
        if connection:
            connection.rollback()

        print(
            "\nETL error:"
        )
        print(error)

        sys.exit(1)

    finally:
        if connection:
            connection.close()
            print("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()