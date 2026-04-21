-- ============================================================
-- GOLD LAYER: Athena Views for Norway Car Sales Lakehouse
-- ============================================================
-- These views sit on top of the Silver Layer (Apache Iceberg)
-- and provide pre-aggregated, business-ready datasets.
--
-- Database: lakehouse_db
-- Silver Table: norway_car_sales_silver (Iceberg, partitioned by year)
-- Quarantine Bucket: car-sales-lakehouse-quar-324037321692
--
-- IMPORTANT: Views are computed at query-time (no storage cost).
-- In production with >1TB datasets, consider materializing via
-- CTAS or dbt incremental models for sub-second latency.
-- ============================================================


-- ============================================================
-- VIEW 1: gold_market_leaders
-- Question: "Who are the Top N brands by year in sales volume?"
-- ============================================================
-- Uses RANK() instead of ROW_NUMBER() so tied brands share the
-- same position. This avoids misleading rankings in tight markets.
-- ============================================================
CREATE OR REPLACE VIEW lakehouse_db.gold_market_leaders AS
SELECT 
    year,
    make,
    SUM(quantity) AS total_units,
    ROUND(SUM(pct), 2) AS total_market_share,
    RANK() OVER (PARTITION BY year ORDER BY SUM(quantity) DESC) AS ranking
FROM lakehouse_db.norway_car_sales_silver
GROUP BY year, make;


-- ============================================================
-- VIEW 2: gold_yoy_growth
-- Question: "Which brands are growing or shrinking year-over-year?"
-- ============================================================
-- LEFT JOIN ensures brands appearing for the first time show NULL
-- for prev_year_units (no artificial zero). NULLIF prevents
-- division-by-zero when a brand had 0 sales the previous year.
-- ============================================================
CREATE OR REPLACE VIEW lakehouse_db.gold_yoy_growth AS
WITH yearly AS (
    SELECT year, make, SUM(quantity) AS total_units
    FROM lakehouse_db.norway_car_sales_silver
    GROUP BY year, make
)
SELECT 
    curr.year,
    curr.make,
    curr.total_units,
    prev.total_units AS prev_year_units,
    ROUND(
        CAST((curr.total_units - prev.total_units) AS DOUBLE) 
        / NULLIF(prev.total_units, 0) * 100, 2
    ) AS yoy_growth_pct
FROM yearly curr
LEFT JOIN yearly prev 
    ON curr.make = prev.make 
   AND curr.year = prev.year + 1;


-- ============================================================
-- VIEW 3: gold_monthly_trend
-- Question: "What is the market's seasonality? Which months sell more?"
-- ============================================================
-- Aggregates total market volume per month across all brands.
-- The active_brands count helps detect data completeness issues
-- (if a month suddenly has fewer brands, data may be missing).
-- ============================================================
CREATE OR REPLACE VIEW lakehouse_db.gold_monthly_trend AS
SELECT 
    year,
    month,
    SUM(quantity) AS total_market_units,
    COUNT(DISTINCT make) AS active_brands
FROM lakehouse_db.norway_car_sales_silver
GROUP BY year, month;


-- ============================================================
-- VIEW 4: gold_brand_concentration
-- Question: "Is the market becoming more concentrated or diversified?"
-- ============================================================
-- Uses the Herfindahl-Hirschman Index (HHI): sum of squared 
-- market shares. Used by antitrust regulators worldwide.
--   HHI < 1500  → Competitive market
--   1500 - 2500 → Moderate concentration
--   > 2500      → Highly concentrated
-- ============================================================
CREATE OR REPLACE VIEW lakehouse_db.gold_brand_concentration AS
WITH market_shares AS (
    SELECT 
        year,
        make,
        CAST(SUM(quantity) AS DOUBLE) / SUM(SUM(quantity)) OVER (PARTITION BY year) * 100 AS market_share_pct
    FROM lakehouse_db.norway_car_sales_silver
    GROUP BY year, make
)
SELECT 
    year,
    COUNT(DISTINCT make) AS total_brands,
    ROUND(SUM(POWER(market_share_pct, 2)), 2) AS hhi_index,
    ROUND(MAX(market_share_pct), 2) AS top_brand_share_pct
FROM market_shares
GROUP BY year;


-- ============================================================
-- VIEW 5: gold_emerging_brands
-- Question: "Which brands entered the market recently and are growing fast?"
-- ============================================================
-- Filters for brands whose first appearance was 2015 or later.
-- Designed to spotlight EV disruptors like Tesla, BYD, Polestar.
-- ============================================================
CREATE OR REPLACE VIEW lakehouse_db.gold_emerging_brands AS
WITH brand_first_year AS (
    SELECT make, MIN(year) AS entry_year
    FROM lakehouse_db.norway_car_sales_silver
    GROUP BY make
),
brand_yearly AS (
    SELECT year, make, SUM(quantity) AS total_units
    FROM lakehouse_db.norway_car_sales_silver
    GROUP BY year, make
)
SELECT 
    by2.year,
    by2.make,
    bf.entry_year,
    by2.total_units,
    ROUND(
        CAST((by2.total_units - by1.total_units) AS DOUBLE) 
        / NULLIF(by1.total_units, 0) * 100, 2
    ) AS yoy_growth_pct
FROM brand_yearly by2
JOIN brand_first_year bf ON by2.make = bf.make
LEFT JOIN brand_yearly by1 
    ON by2.make = by1.make 
   AND by2.year = by1.year + 1
WHERE bf.entry_year >= 2015;


-- ============================================================
-- EXTERNAL TABLE: quarantine_records
-- Purpose: Expose Pydantic validation rejects stored in S3
-- ============================================================
-- The ingestion Lambda writes rejected records as Parquet files
-- into s3://<quarantine-bucket>/ingestion_date=YYYYMMDD/.
-- All columns are stored as STRING because the original data
-- failed type validation (e.g. Quantity could be "abc").
--
-- Uses Hive-style partitioning (ingestion_date= prefix) so
-- Athena can prune scans by ingestion date automatically.
-- ============================================================
CREATE EXTERNAL TABLE IF NOT EXISTS lakehouse_db.quarantine_records (
    `Year`               STRING,
    `Month`              STRING,
    `Make`               STRING,
    `Quantity`           STRING,
    `Pct`                STRING,
    `validation_errors`  STRING
)
PARTITIONED BY (`ingestion_date` STRING)
STORED AS PARQUET
LOCATION 's3://car-sales-lakehouse-quar-324037321692/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');


-- ============================================================
-- Partition Discovery: MSCK REPAIR TABLE
-- Athena needs this to detect the ingestion_date=YYYYMMDD/
-- prefixes in S3 and register them as queryable partitions.
-- Without this command, the quarantine_records table returns
-- zero rows even if the data exists in S3.
-- ============================================================
MSCK REPAIR TABLE lakehouse_db.quarantine_records;


-- ============================================================
-- VIEW 6: gold_quality_metrics
-- Question: "How healthy is our data pipeline? What errors does Pydantic catch?"
-- ============================================================
-- Summarizes quarantine data by ingestion date, counting total
-- rejects and breaking down by error type. This powers the
-- "Pipeline Health" page in the Streamlit dashboard.
-- ============================================================
CREATE OR REPLACE VIEW lakehouse_db.gold_quality_metrics AS
SELECT 
    ingestion_date,
    COUNT(*) AS rejected_count,
    COUNT(CASE WHEN validation_errors LIKE '%Quantity%' THEN 1 END) AS quantity_errors,
    COUNT(CASE WHEN validation_errors LIKE '%Make%' THEN 1 END) AS make_errors,
    COUNT(CASE WHEN validation_errors LIKE '%Year%' THEN 1 END) AS year_errors,
    COUNT(CASE WHEN validation_errors LIKE '%Month%' THEN 1 END) AS month_errors
FROM lakehouse_db.quarantine_records
GROUP BY ingestion_date;
