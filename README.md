# SwiftDash Food Delivery — Operations & Customer Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-40%20passing-brightgreen)]()
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)](https://mysql.com)
[![Power BI](https://img.shields.io/badge/Power%20BI-DAX-yellow?logo=powerbi)](https://powerbi.microsoft.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

End-to-end analytics project for a food delivery platform. Covers the full workflow — data generation, cleaning, SQL analysis, and an interactive Power BI dashboard — using Python, MySQL, and Power BI.

Built as a portfolio project for **Data Analyst / BI Analyst / Business Analyst** internship and placement interviews.

---

## Quick Look

| Metric | Value |
|--------|-------|
| Orders analysed | 65,000+ |
| Customers | 12,000 |
| Restaurants | 250 |
| Delivery partners | 800 |
| Cities | 15 |
| SQL queries | 50 |
| Test coverage | 40 unit & integration tests |

---

## Repository Structure

```
swiftdash-ops-analytics/
│
├── run_pipeline.py          # One-command pipeline runner
├── config.py                # Centralised paths & constants
├── requirements.txt
├── LICENSE
├── CONTRIBUTING.md
│
├── scripts/
│   ├── generate_data.py           # Synthetic data generation
│   ├── clean_data.py              # Data cleaning & validation
│   ├── feature_engineering.py     # RFM, segments, aggregations
│   ├── generate_visualizations.py # EDA chart exports
│   └── load_to_mysql.py           # MySQL bulk loader
│
├── notebooks/
│   └── 01_exploratory_data_analysis.ipynb
│
├── sql/
│   ├── 01_schema.sql              # DB schema (6 tables, FKs, indexes)
│   ├── 02_revenue_analysis.sql    # 10 revenue queries
│   ├── 03_customer_analysis.sql   # 10 customer queries
│   ├── 04_operational_analysis.sql# 10 operations queries
│   ├── 05_restaurant_analysis.sql # 10 restaurant queries
│   └── 06_kpi_dashboard.sql       # 10 KPI & executive queries
│
├── docs/
│   ├── data_dictionary.md         # Column-level documentation
│   └── er_diagram.md              # Entity-relationship diagram (Mermaid)
│
├── dashboard/
│   ├── swiftdash_measures.dax     # DAX measures (copy-paste into Power BI)
│   └── swiftdash_dashboard.pbix   # Power BI file (build per guide below)
│
├── tests/
│   ├── test_cleaning.py           # 20 data cleaning tests
│   ├── test_features.py           # 4 feature engineering tests
│   └── test_pipeline_integrity.py # 16 pipeline integrity tests
│
├── reports/
│   ├── business_recommendations.md
│   ├── power_bi_dashboard_guide.md
│   ├── interview_questions.md
│   └── resume_bullets.md
│
├── screenshots/                   # EDA & dashboard exports
└── logs/                          # Pipeline execution logs
```

---

## Pipeline

```
                        ┌──────────────┐
                        │  config.py   │
                        └──────┬───────┘
                               │
                   ┌───────────┴───────────┐
                   │    run_pipeline.py     │
                   └───────────┬───────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
  generate_data.py      clean_data.py      feature_engineering.py
         │                     │                     │
    Raw CSVs             Cleaned CSVs           Processed tables
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                        load_to_mysql.py
                               │
                          MySQL DB
                               │
                       50 SQL queries
                               │
                     Power BI dashboard
                               │
                 Business insights & recommendations
```

Run everything with a single command:

```bash
python run_pipeline.py
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.14 |
| Data processing | Pandas, NumPy |
| Visualisation | Matplotlib, Seaborn |
| Database | MySQL 8.0 |
| SQL techniques | CTEs, window functions (`LAG`, `NTILE`, `ROW_NUMBER`), cohort analysis, self-joins, conditional aggregation |
| Dashboard | Power BI (DAX measures, drill-through, time intelligence, slicers) |
| Testing | pytest (40 tests) |
| Logging | Python `logging` module → `logs/pipeline.log` |
| Version control | Git, GitHub |

---

## Dataset

Synthetically generated using Faker + NumPy with realistic distributions: peak-hour ordering, weekday/weekend variation, weather impact on delivery times, and seasonal trends.

| Table | Rows | Key columns |
|-------|------|-------------|
| `customers` | 12,000 | age, gender, city, signup_date, is_active |
| `restaurants` | 250 | cuisine_type, rating, preparation_time_mins |
| `drivers` | 800 | vehicle_type, rating, is_active |
| `orders` | 65,000 | total_amount, payment_method, order_status, surge_multiplier |
| `order_items` | 134,383 | item_name, category, quantity, unit_price |
| `delivery_logs` | 59,767 | travel_time_mins, distance_km, traffic, weather, is_on_time |

[Full data dictionary](docs/data_dictionary.md) · [ER diagram](docs/er_diagram.md)

---

## Database Schema (MySQL)

Six tables with foreign keys, indexes, `ON DELETE` rules, and audit timestamps:

```
customers  1───* orders *───1 restaurants
                   │
                   *
             order_items
                   │
                   1
                   │
            delivery_logs  *───1 drivers
```

- **`ON DELETE RESTRICT`** on customer/restaurant FKs (prevents orphan orders)
- **`ON DELETE SET NULL`** on driver FK (cancelled orders have no driver)
- **`ON DELETE CASCADE`** on order_items / delivery_logs (clean deletion)
- Indexes on `order_date`, `customer_id`, `restaurant_id`, `order_status`, `payment_method`
- `created_at` / `updated_at` timestamps on every table

---

## SQL Analysis — 50 Queries

### Revenue (10 queries)
Monthly revenue with MoM growth (`LAG`), revenue by payment method / city / hour / cuisine, revenue lost to cancellations, discount impact analysis, weekday vs weekend comparison.

### Customer (10 queries)
RFM segmentation (Platinum/Gold/Silver/At Risk/Churned with documented thresholds), customer lifetime value ranking, repeat customer rate, cohort retention analysis, age/gender analysis, acquisition trends, preferred payment methods.

### Operations (10 queries)
Delivery time by hour / traffic / weather, driver efficiency ranking, vehicle type comparison, peak hour analysis, outlier detection (deliveries > 60 min), refund rate (CTE-based).

### Restaurant (10 queries)
Top restaurants by revenue, cuisine performance, most popular items, cross-selling analysis (self-join market basket), cancellation rate by restaurant, revenue concentration (Pareto via `NTILE`), cuisine popularity by city.

### KPI Dashboard (10 queries)
Executive scorecard, MoM KPI comparison, top 10% customer contribution (`NTILE`), daily active users, payment adoption trends, cohort retention, customer LTV trend, platform economics breakdown, surge pricing analysis, business health scorecard.

---

## Power BI Dashboard

The dashboard specification and all DAX measures are provided. Build it in Power BI Desktop:

1. **Import data:** Load cleaned CSVs (`data/cleaned/*.csv`)
2. **Create Calendar table** using the DAX in `dashboard/swiftdash_measures.dax`
3. **Build relationships** as shown in the ER diagram
4. **Create measures** by copying from `dashboard/swiftdash_measures.dax`
5. **Design 5 pages:**
   - Executive Summary (KPI cards, revenue trend, city chart, payment donut, segment bars)
   - Customer Analytics (treemap, demographics, cohort matrix)
   - Operations & Delivery (delivery time histograms, driver tables, on-time rates)
   - Restaurant & Menu (top restaurants, cuisine treemap, popular items)
   - Trends & Insights (monthly forecast, YoY growth, weekday heatmap)

### Key DAX Measures

```
Total Revenue, Total Orders, Avg Order Value, Cancellation Rate,
On-Time Delivery Rate, Repeat Customer Rate, Avg Customer LTV,
Revenue MoM Growth, Revenue YoY Growth, Revenue Rolling30D,
Revenue MTD/QTD/YTD, Surge Revenue Premium, Peak Hour Orders
```

[Full dashboard build guide](reports/power_bi_dashboard_guide.md)

---

## Dashboard Preview

![Executive Summary Dashboard](screenshots/dashboard_executive_summary.png)

---

## EDA Screenshots

| Monthly Revenue Trend | Customer Segmentation | Top Cuisines |
|:---:|:---:|:---:|
| ![Monthly Revenue](screenshots/monthly_revenue_trend.png) | ![Segmentation](screenshots/customer_segmentation.png) | ![Cuisines](screenshots/top_cuisines.png) |

| Delivery Performance | Time Patterns | City Revenue |
|:---:|:---:|:---:|
| ![Delivery](screenshots/delivery_performance.png) | ![Patterns](screenshots/time_patterns.png) | ![Cities](screenshots/city_revenue.png) |

---

## Key Insights

**Revenue:** Monthly revenue shows consistent growth with seasonal Q4 peaks. UPI dominates at ~45% of transactions. Discounts under INR 50 show the best ROI; deep discounts (>INR 150) show diminishing returns.

**Customers:** Top 10% of customers contribute ~35-40% of revenue. Platinum + Gold segments (15% of customers) drive 40%+ of revenue. First-month retention drops to ~35-40% — a key improvement area. Age 25-34 is the highest-value segment.

**Operations:** Average delivery time: 25-35 minutes. Motorcycles outperform cars in high traffic (88% vs 72% on-time). Gridlock reduces on-time rates below 60%. Heavy rain increases delivery time by 30%+ and doubles cancellations.

**Restaurants:** North Indian, South Indian, and Chinese cuisines drive 60%+ of total revenue. Restaurants with prep time >30 min have 2x higher cancellation rates. Top 20% of restaurants contribute ~65% of revenue (Pareto).

---

## Business Recommendations

| Priority | Initiative | Expected Impact |
|----------|-----------|----------------|
| P0 | Tiered loyalty program (Platinum/Gold/Silver) | +15% retention, +10% revenue |
| P0 | Dynamic delivery dispatch (more scooters at peak) | +8% on-time rate |
| P1 | Shift from broad discounts to targeted rewards | +5% margin |
| P1 | Marketing investment in high-growth Tier-2 cities | +20% user growth |
| P1 | Reactivation campaigns for At Risk customers | Recover ~15% of churned users |
| P2 | Weather contingency planning (pre-position drivers) | -10% rain-day cancellations |

[Full recommendations report](reports/business_recommendations.md)

---

## Testing

```bash
pytest tests/ -v
# 40 passed
```

- **test_cleaning.py (20 tests):** null handling, outlier clipping, type standardisation, domain validation
- **test_features.py (4 tests):** RFM computation, empty-data edge case, driver scoring, time-series aggregation
- **test_pipeline_integrity.py (16 tests):** file existence, row counts, FK integrity, null-key checks

---

## Setup

```bash
# Clone
git clone https://github.com/ShivShah018/food-delivery-operations-analytics.git
cd food-delivery-operations-analytics

# Install dependencies
pip install -r requirements.txt

# Run full pipeline
python run_pipeline.py

# Run tests
pytest tests/ -v

# Open EDA notebook
jupyter notebook notebooks/01_exploratory_data_analysis.ipynb
```

### MySQL (optional)

```sql
-- In your MySQL client
SOURCE sql/01_schema.sql;
```

Then: `python run_pipeline.py` (the MySQL step runs automatically unless you pass `--skip-db`).

### Power BI

1. Open Power BI Desktop
2. Get Data → Text/CSV → select files from `data/cleaned/`
3. Create Calendar table and measures from `dashboard/swiftdash_measures.dax`
4. Build pages following [`reports/power_bi_dashboard_guide.md`](reports/power_bi_dashboard_guide.md)

---

## Skills Demonstrated

- **Python:** Pipeline design, data validation, feature engineering, logging, error handling
- **SQL:** Schema design, window functions, CTEs, cohort analysis, query optimisation
- **Power BI:** DAX measures, data modelling, interactive dashboard design, drill-through
- **Data analysis:** EDA, RFM segmentation, correlation analysis, trend decomposition
- **Testing:** pytest, edge-case coverage, data integrity assertions
- **Engineering:** Modular code, centralised config, one-command pipeline, structured logging
- **Business:** Insight generation, quantified recommendations, implementation roadmapping

---

## Resume-Ready Bullet Points

> Built an end-to-end food delivery analytics platform analysing 65K+ orders across 15 cities using Python (Pandas/NumPy), MySQL, and Power BI.

> Engineered RFM-based customer segmentation (12K customers) and driver efficiency scores, identifying 6 behavioural segments for targeted marketing.

> Wrote 50 analytical SQL queries using window functions, CTEs, and cohort analysis for revenue, retention, and operational KPIs.

> Designed a 5-page Power BI dashboard with 15+ DAX measures, drill-through, and time intelligence for executive decision-making.

> Delivered 6 prioritised business recommendations with quantified ROI, targeting a projected 15% retention improvement and 10% revenue growth.

---

## Additional Resources

- [Data Dictionary](docs/data_dictionary.md)
- [ER Diagram](docs/er_diagram.md)
- [Business Recommendations](reports/business_recommendations.md)
- [Power BI Dashboard Guide](reports/power_bi_dashboard_guide.md)
- [Interview Questions](reports/interview_questions.md) — 22 likely interview Q&As
- [Resume Bullet Points](reports/resume_bullets.md)
- [Development Roadmap](DEVELOPMENT_ROADMAP.md)

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built for placement interviews. Contributions and forks welcome.*
