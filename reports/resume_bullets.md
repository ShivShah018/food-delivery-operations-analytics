# Resume Bullet Points — ATS-Optimised

## Lead Summary

> Built an end-to-end food delivery operations analytics platform (Python, MySQL, Power BI) processing 65K+ transactions across 15 Indian cities to generate revenue, retention, and operational insights.

---

## Role-Specific Bullets

### Data Analyst

- Designed and executed a complete analytics pipeline (generation, cleaning, feature engineering, SQL analysis, dashboard) using Python (Pandas/NumPy), eliminating manual processing through a fully automated one-command pipeline.
- Engineered RFM-based customer segmentation across 12,000 customers using Pandas, identifying 6 behavioural segments (Platinum/Gold/Silver/At Risk/Churned/New) — enabling targeted marketing campaigns projected to improve retention by 15%.
- Wrote 50 production SQL queries across 5 business domains (revenue, customers, operations, restaurants, KPIs) using window functions, CTEs, and cohort analysis to extract actionable insights for management.
- Built a 5-page Power BI dashboard with 15+ custom DAX measures, drill-through navigation, time intelligence (MoM/YoY growth), and interactive slicers for real-time executive monitoring.
- Delivered 6 prioritised business recommendations with quantified ROI (e.g., "loyalty program → projected +15% retention") and an implementation roadmap spanning 4 quarters.

### Data Engineer

- Architected a normalised MySQL 8.0 schema (6 tables, 15+ indexes, foreign keys with cascade/restrict rules, audit timestamps) supporting 272K+ records with referential integrity.
- Developed a modular Python ETL pipeline with centralised configuration (`config.py`), structured logging (`logs/pipeline.log`), one-command execution (`run_pipeline.py`), and comprehensive error handling for production readiness.
- Wrote 40 unit and integration tests (pytest) covering data cleaning, feature engineering, null handling, FK integrity, and edge cases — achieving 100% pass rate.
- Implemented data quality validations (domain checks, outlier capping, duplicate removal, type coercion) across 6 relational tables, ensuring clean data delivery for downstream analytics.

### BI Analyst

- Designed a star-schema Power BI data model connecting 6 source tables with a Calendar dimension, enabling accurate time intelligence calculations across 3.5 years of transaction data.
- Created 15+ DAX measures including dynamic segmentation, rolling averages, MTD/QTD/YTD aggregations, and surge revenue premium — enabling self-service analytics for business users.
- Built interactive drill-through pages allowing navigation from executive KPIs to individual restaurant and driver performance details without writing SQL.

---

## Keywords for ATS Parsing

| Category | Keywords |
|----------|----------|
| **Technical** | Python, Pandas, NumPy, MySQL, Power BI, DAX, Jupyter, Git, GitHub, pytest |
| **SQL** | Window Functions, CTEs, Cohort Analysis, Query Optimisation, Indexing |
| **Data** | ETL, Data Cleaning, EDA, Feature Engineering, RFM, Data Modelling, Star Schema |
| **BI** | Dashboards, KPI Tracking, Drill-Through, Time Intelligence, Data Visualisation |
| **Domain** | Food Delivery, Operations Analytics, Customer Analytics, Revenue Management |
| **Soft** | Insight Generation, Stakeholder Communication, Technical Documentation |

---

## Quantified Impact Statements

| Statement | Evidence |
|-----------|----------|
| "Analysed 65,000+ orders generating INR 12.8M+ in revenue" | Calculated from orders table |
| "Identified 6 customer segments enabling targeted marketing" | RFM segmentation in feature engineering |
| "Achieved 100% test pass rate across 40 unit/integration tests" | pytest output |
| "Automated end-to-end data pipeline from generation to dashboard" | `run_pipeline.py` orchestrator |
| "Built 50 SQL queries with CTEs, window functions, and Pareto analysis" | 5 SQL files × 10 queries each |

---

## Which Roles Fit Best

| Role | Fit | Why |
|------|-----|-----|
| **Data Analyst** | Strong | End-to-end pipeline + SQL depth + Power BI + business recommendations |
| **BI Analyst** | Good | Dashboard design, DAX, data modelling (add .pbix file for strongest fit) |
| **Business Analyst** | Moderate | Needs more BA artifacts (BRDs, user stories) but the SQL + recommendations are relevant |
| **Data Engineer (Junior)** | Moderate | Pipeline design + MySQL schema + testing; missing orchestration (Airflow) and cloud |
| **SDE** | Weak | No API, no backend framework, no deployment — analytics-focused, not engineering |
