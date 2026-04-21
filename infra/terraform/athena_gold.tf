# ==========================================
# Athena Named Queries: Gold Layer Documentation
# ==========================================
# Named Queries appear in the Athena Console under "Saved Queries".
# They serve as documentation and quick-access shortcuts for analysts.
# IMPORTANT: Named Queries do NOT auto-execute. They are created by
# the deploy_gold_views.py script using StartQueryExecution.
# ==========================================

resource "aws_athena_named_query" "gold_market_leaders" {
  name        = "Gold: Market Leaders by Year"
  description = "Top brands ranked by total units sold per year (RANK window function)"
  database    = aws_glue_catalog_database.lakehouse_db.name
  workgroup   = aws_athena_workgroup.lakehouse_workgroup.name
  query       = <<-EOQ
    SELECT * FROM lakehouse_db.gold_market_leaders
    WHERE year = 2023
    ORDER BY ranking ASC
    LIMIT 10;
  EOQ
}

resource "aws_athena_named_query" "gold_yoy_growth" {
  name        = "Gold: Year-over-Year Growth"
  description = "Brand sales growth percentage compared to previous year"
  database    = aws_glue_catalog_database.lakehouse_db.name
  workgroup   = aws_athena_workgroup.lakehouse_workgroup.name
  query       = <<-EOQ
    SELECT * FROM lakehouse_db.gold_yoy_growth
    WHERE year = 2023
    ORDER BY yoy_growth_pct DESC NULLS LAST
    LIMIT 20;
  EOQ
}

resource "aws_athena_named_query" "gold_monthly_trend" {
  name        = "Gold: Monthly Market Trend"
  description = "Total market sales per month with active brand count"
  database    = aws_glue_catalog_database.lakehouse_db.name
  workgroup   = aws_athena_workgroup.lakehouse_workgroup.name
  query       = <<-EOQ
    SELECT * FROM lakehouse_db.gold_monthly_trend
    ORDER BY year DESC, month DESC
    LIMIT 24;
  EOQ
}

resource "aws_athena_named_query" "gold_brand_concentration" {
  name        = "Gold: Market Concentration (HHI)"
  description = "Herfindahl-Hirschman Index measuring market concentration over time"
  database    = aws_glue_catalog_database.lakehouse_db.name
  workgroup   = aws_athena_workgroup.lakehouse_workgroup.name
  query       = <<-EOQ
    SELECT * FROM lakehouse_db.gold_brand_concentration
    ORDER BY year DESC;
  EOQ
}

resource "aws_athena_named_query" "gold_emerging_brands" {
  name        = "Gold: Emerging Brands (post-2015)"
  description = "New market entrants since 2015 with YoY growth rates"
  database    = aws_glue_catalog_database.lakehouse_db.name
  workgroup   = aws_athena_workgroup.lakehouse_workgroup.name
  query       = <<-EOQ
    SELECT * FROM lakehouse_db.gold_emerging_brands
    WHERE year = 2023
    ORDER BY total_units DESC;
  EOQ
}

resource "aws_athena_named_query" "gold_quality_metrics" {
  name        = "Gold: Pipeline Quality Metrics"
  description = "Pydantic validation reject summary by ingestion date and error type"
  database    = aws_glue_catalog_database.lakehouse_db.name
  workgroup   = aws_athena_workgroup.lakehouse_workgroup.name
  query       = <<-EOQ
    SELECT * FROM lakehouse_db.gold_quality_metrics
    ORDER BY ingestion_date DESC;
  EOQ
}
