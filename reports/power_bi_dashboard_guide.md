# SwiftDash Power BI Dashboard — Build Guide

## Overview

The Power BI dashboard provides an interactive executive view of SwiftDash's food delivery operations. It is designed for:
- **Executives:** High-level KPIs, revenue trends, market performance
- **Operations Managers:** Delivery performance, driver efficiency, city-wise metrics
- **Marketing Teams:** Customer segments, cuisine trends, discount effectiveness

---

## Dashboard Structure

### Page 1: Executive Summary

**Layout:**
```
+--------------------------------------------------+
|  [Logo]  SwiftDash Operations Dashboard    [Slicers] |
+--------------------------------------------------+
| KPI: Total Rev | KPI: Orders | KPI: AOV | KPI: On-Time % | KPI: Cancellation % |
+--------------------------------------------------+
|                    |                                |
|  Monthly Revenue   |  Orders & Customers Trend     |
|  Trend (Line)      |  (Dual Axis Line)             |
|                    |                                |
+--------------------------------------------------+
|                    |                                |
|  Revenue by City   |  Payment Method Distribution  |
|  (Bar Chart)       |  (Donut Chart)                |
|                    |                                |
+--------------------------------------------------+
```

**Slicers:** Year, Quarter, City, Cuisine Type

### Page 2: Customer Analytics

**Layout:**
```
+--------------------------------------------------+
|  Customer Analytics                    [Slicers]    |
+--------------------------------------------------+
|  Customer Segment    |  Age/Gender Distribution   |
|  (Treemap)           |  (Stacked Bar)             |
|                      |                            |
+--------------------------------------------------+
|                      |                            |
|  Top Customers by    |  Repeat Rate Trend         |
|  Lifetime Value      |  (Line Chart)              |
|  (Table)             |                            |
|                      |                            |
+--------------------------------------------------+
|  Customer Acquisition | Cohort Retention Table    |
|  (Area Chart)        |  (Matrix)                  |
+--------------------------------------------------+
```

**Drill-down:** City -> Customer Segment -> Individual Customer

### Page 3: Operations & Delivery

**Layout:**
```
+--------------------------------------------------+
|  Operations Dashboard                  [Slicers]    |
+--------------------------------------------------+
| KPI: Avg Delivery | KPI: On-Time % | KPI: Cancellation % |
+--------------------------------------------------+
|                    |                                |
|  Delivery Time by  |  On-Time Rate by Traffic/     |
|  Hour (Bar)        |  Weather (Clustered Bar)      |
|                    |                                |
+--------------------------------------------------+
|                    |                                |
|  Driver Efficiency |  City Operations Summary      |
|  (Table + KPI)     |  (Map with bubbles)           |
|                    |                                |
+--------------------------------------------------+
```

**Drill-down:** City -> Driver -> Individual Delivery

### Page 4: Restaurant & Menu

**Layout:**
```
+--------------------------------------------------+
|  Restaurant Analytics                   [Slicers]   |
+--------------------------------------------------+
|                    |                                |
|  Top Restaurants   |  Cuisine Revenue Share        |
|  (Bar Chart)       |  (Treemap)                    |
|                    |                                |
+--------------------------------------------------+
|                    |                                |
|  Most Ordered Items|  Restaurant Rating vs Orders  |
|  (Horizontal Bar)  |  (Scatter Plot)               |
|                    |                                |
+--------------------------------------------------+
|  Cancellation Rate by Restaurant (Table)           |
+--------------------------------------------------+
```

### Page 5: Trends & Forecasting

**Layout:**
```
+--------------------------------------------------+
|  Trends & Insights                     [Slicers]    |
+--------------------------------------------------+
|                    |                                |
|  Monthly Revenue   |  YoY Growth Comparison        |
|  (Line + Forecast) |  (Waterfall or Bar)           |
|                    |                                |
+--------------------------------------------------+
|                    |                                |
|  Weekday/Hourly    |  Discount Impact Analysis     |
|  Heatmap           |  (Scatter/Bubble)             |
|                    |                                |
+--------------------------------------------------+
```

---

## Data Model

```
customers 1---* orders *---1 restaurants
                     |
                    1
                    |
              order_items
                     |
                     1
                     |
              delivery_logs  *---1 drivers
```

### Key Measures (DAX)

```dax
-- Core KPIs (net revenue — Delivered orders only)
Total Revenue = CALCULATE(SUM(orders[total_amount]), orders[order_status] = "Delivered")
Total Orders = COUNTROWS(orders)
Avg Order Value = AVERAGE(orders[total_amount])
On-Time Delivery % = 
    DIVIDE(
        COUNTROWS(FILTER(delivery_logs, delivery_logs[is_on_time] = TRUE)),
        COUNTROWS(delivery_logs)
    ) * 100
Cancellation Rate = 
    DIVIDE(
        COUNTROWS(FILTER(orders, orders[order_status] = "Cancelled")),
        COUNTROWS(orders)
    ) * 100

-- Time Intelligence
Revenue MoM Growth = 
    VAR CurrentMonth = [Total Revenue]
    VAR PrevMonth = CALCULATE([Total Revenue], PREVIOUSMONTH('calendar'[Date]))
    RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth)

Revenue YoY Growth = 
    VAR CurrentPeriod = [Total Revenue]
    VAR PrevPeriod = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR('calendar'[Date]))
    RETURN DIVIDE(CurrentPeriod - PrevPeriod, PrevPeriod)

-- Customer Metrics
Repeat Customer Rate = 
    VAR RepeatCustomers = 
        COUNTROWS(
            FILTER(
                VALUES(orders[customer_id]),
                CALCULATE(COUNTROWS(orders)) > 1
            )
        )
    VAR AllCustomers = DISTINCTCOUNT(orders[customer_id])
    RETURN DIVIDE(RepeatCustomers, AllCustomers)

Avg Customer LTV = 
    DIVIDE(
        SUM(orders[total_amount]),
        DISTINCTCOUNT(orders[customer_id])
    )

-- Operational
Avg Delivery Time = AVERAGE(delivery_logs[travel_time_mins])
Peak Hour Orders = 
    MAXX(
        GROUPBY(orders, orders[order_hour], "Orders", COUNTROWS(CURRENTGROUP)),
        [Orders]
    )
```

---

## Visuals Checklist

| Visual Type | Page | Purpose |
|------------|------|---------|
| KPI Cards | 1, 3 | Key metrics at a glance |
| Line Chart | 1,5 | Revenue/order trends |
| Stacked Bar | 2 | Demographics |
| Donut/Pie | 1,4 | Payment/cuisine share |
| Treemap | 2,4 | Segment/cuisine hierarchy |
| Map | 3 | City performance |
| Scatter | 4 | Rating vs orders |
| Matrix | 2 | Cohort retention |
| Table | 2,3,4 | Top lists, details |
| Heatmap | 5 | Hour/weekday patterns |
| Slicers | All | Interactive filtering |
| Drill-through | 2,3 | Deep dive into details |

---

## Color Palette

```dax
Primary Blue:    #3498DB
Success Green:   #2ECC71
Warning Orange:  #F39C12
Danger Red:      #E74C3C
Dark Text:       #2C3E50
Light BG:        #F8F9FA
Platinum:        #2C3E50
Gold:            #F39C12
```

---

## File Structure

- `dashboard/swiftdash_dashboard.pbix` — Power BI file
- `data/cleaned/*.csv` — Source data for Power BI import
- `data/processed/customer_features.csv` — Pre-computed RFM features
- `data/processed/monthly_metrics.csv` — Aggregated time series

### Import Mode

Import all cleaned CSVs into Power BI using **Get Data > Text/CSV**. Also import `data/processed/customer_features.csv` — this is generated by `feature_engineering.py` and contains the RFM segment labels (e.g. `customer_segment`) referenced by the DAX measures. Without this file, measures like `Customer Segment Count` will fail. Configure relationships as shown in data model above. Create a calendar table using:

```dax
Calendar = CALENDAR(DATE(2022,1,1), DATE(2025,6,30))
```

---

## Sharing & Deployment

1. **Publish to Power BI Service** for organization-wide access
2. **Schedule daily refresh** if connected to live MySQL database
3. **Set up Row-Level Security (RLS)** for city-specific views
4. **Export PDF snapshots** for weekly executive reports
5. **Create mobile layout** for on-the-go monitoring
