"""
Deploy Gold Layer Views to Amazon Athena.

Reads the gold_views.sql file, splits it by semicolons,
and executes each DDL statement against the Athena engine
using boto3. Waits for each query to complete before
proceeding to the next one.

Usage:
    python scripts/deploy_gold_views.py

Requirements:
    - AWS credentials configured (CLI or environment variables)
    - Athena workgroup and Glue Catalog database must already exist
    - Silver layer Iceberg table must already be populated
"""
import boto3
import time
import sys
import os
from pathlib import Path

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ============================================================
# Configuration
# ============================================================
DATABASE = "lakehouse_db"
WORKGROUP = "car-sales-lakehouse-workgroup"
REGION = "us-east-1"

# Path to the SQL file relative to this script
SQL_FILE = Path(__file__).parent.parent / "src" / "transform" / "gold_views.sql"

# Maximum time to wait for a single query (seconds)
QUERY_TIMEOUT = 60

# Polling interval (seconds)
POLL_INTERVAL = 2


def read_sql_statements(sql_path: Path) -> list[str]:
    """
    Parse the SQL file into individual statements.

    Splits on semicolons, strips whitespace, and filters out
    empty strings and pure comment blocks.
    """
    raw_sql = sql_path.read_text(encoding="utf-8")

    # Split by semicolons and clean up
    statements = [stmt.strip() for stmt in raw_sql.split(";")]

    # Filter out empty statements and comment-only blocks
    valid_statements = []
    for stmt in statements:
        # Remove all comment lines to check if there's actual SQL
        sql_lines = [
            line for line in stmt.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        if sql_lines:
            valid_statements.append(stmt)

    return valid_statements


def extract_statement_name(statement: str) -> str:
    """
    Extract a human-readable name from the SQL statement.
    Looks for CREATE VIEW/TABLE names in the DDL.
    """
    upper = statement.upper()
    if "CREATE OR REPLACE VIEW" in upper:
        # Extract: CREATE OR REPLACE VIEW lakehouse_db.gold_xxx AS
        parts = statement.split()
        for i, part in enumerate(parts):
            if part.upper() == "VIEW":
                return parts[i + 1].replace("lakehouse_db.", "")
    elif "CREATE EXTERNAL TABLE" in upper:
        parts = statement.split()
        for i, part in enumerate(parts):
            if part.upper() == "TABLE":
                # Skip optional "IF NOT EXISTS"
                name_idx = i + 1
                while parts[name_idx].upper() in ("IF", "NOT", "EXISTS"):
                    name_idx += 1
                return parts[name_idx].replace("lakehouse_db.", "")
    elif "MSCK REPAIR TABLE" in upper:
        return "MSCK_REPAIR_TABLE"
    return "unknown_statement"


def execute_query(
    client: boto3.client,
    sql: str,
    name: str,
) -> bool:
    """
    Execute a single Athena query and wait for completion.

    Returns True if the query succeeded, False otherwise.
    """
    print(f"\n{'='*60}")
    print(f"  Deploying: {name}")
    print(f"{'='*60}")

    try:
        response = client.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": DATABASE},
            WorkGroup=WORKGROUP,
        )
    except Exception as e:
        print(f"  [FAIL] Failed to start query: {e}")
        return False

    execution_id = response["QueryExecutionId"]
    print(f"  Execution ID: {execution_id}")

    # Poll until completion or timeout
    elapsed = 0
    while elapsed < QUERY_TIMEOUT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        result = client.get_query_execution(
            QueryExecutionId=execution_id
        )
        state = result["QueryExecution"]["Status"]["State"]

        if state == "SUCCEEDED":
            stats = result["QueryExecution"].get("Statistics", {})
            scan_bytes = stats.get("DataScannedInBytes", 0)
            exec_time = stats.get("EngineExecutionTimeInMillis", 0)
            print(f"  [OK] SUCCEEDED in {exec_time}ms | Scanned: {scan_bytes} bytes")
            return True
        elif state in ("FAILED", "CANCELLED"):
            reason = result["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown"
            )
            print(f"  [FAIL] {state}: {reason}")
            return False

        print(f"  ... {state} ({elapsed}s)")

    print(f"  [FAIL] TIMEOUT after {QUERY_TIMEOUT}s")
    return False


def main() -> None:
    """Deploy all Gold Layer views to Athena."""
    print("=" * 60)
    print("  Gold Layer Deployment - Athena Views")
    print(f"  Database:  {DATABASE}")
    print(f"  Workgroup: {WORKGROUP}")
    print(f"  Region:    {REGION}")
    print("=" * 60)

    if not SQL_FILE.exists():
        print(f"\n[FAIL] SQL file not found: {SQL_FILE}")
        sys.exit(1)

    statements = read_sql_statements(SQL_FILE)
    print(f"\nFound {len(statements)} SQL statements to execute.")

    client = boto3.client("athena", region_name=REGION)

    succeeded = 0
    failed = 0
    results: list[tuple[str, bool]] = []

    for i, stmt in enumerate(statements, 1):
        name = extract_statement_name(stmt)
        print(f"\n[{i}/{len(statements)}]", end="")

        success = execute_query(client, stmt, name)
        results.append((name, success))

        if success:
            succeeded += 1
        else:
            failed += 1

    # Summary report
    print(f"\n\n{'='*60}")
    print("  Deployment Summary")
    print(f"{'='*60}")
    print(f"  Total:     {len(statements)}")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed:    {failed}")
    print(f"\n  Results:")
    for name, success in results:
        icon = "[OK]" if success else "[FAIL]"
        print(f"    {icon} {name}")

    if failed > 0:
        print(f"\n[WARNING] {failed} statement(s) failed. Check errors above.")
        sys.exit(1)
    else:
        print("\nAll Gold Layer views deployed successfully!")


if __name__ == "__main__":
    main()
