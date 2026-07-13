-- ============================================================
-- KPI & EXECUTIVE DASHBOARD QUERIES
-- High-level metrics for business performance monitoring
-- ============================================================

-- 41. Executive Summary KPIs
SELECT
    (SELECT COUNT(DISTINCT customer_id) FROM customers WHERE is_active = 1) AS active_customers,
    (SELECT COUNT(DISTINCT restaurant_id) FROM restaurants WHERE is_active = 1) AS active_restaurants,
    (SELECT COUNT(DISTINCT driver_id) FROM drivers WHERE is_active = 1) AS active_drivers,
    ROUND((SELECT SUM(total_amount) FROM orders WHERE order_status = 'Delivered'), 2) AS total_revenue,
    (SELECT COUNT(*) FROM orders WHERE order_status = 'Delivered') AS total_delivered_orders,
    ROUND((SELECT AVG(total_amount) FROM orders WHERE order_status = 'Delivered'), 2) AS avg_order_value,
    ROUND((SELECT SUM(discount) * 100.0 / NULLIF(SUM(total_amount + discount), 0)
           FROM orders WHERE order_status = 'Delivered'), 2) AS overall_discount_rate_pct,
    ROUND((SELECT SUM(CASE WHEN is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
           FROM delivery_logs), 2) AS overall_on_time_rate_pct,
    ROUND((SELECT AVG(customer_rating) FROM orders WHERE customer_rating IS NOT NULL), 2) AS avg_customer_rating,
    ROUND((SELECT SUM(total_amount) FROM orders WHERE order_status = 'Cancelled'), 2) AS revenue_lost_to_cancellations;

-- 42. Month-over-Month KPI Comparison
WITH monthly_kpis AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS year_month,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(SUM(total_amount), 2) AS revenue,
        ROUND(AVG(total_amount), 2) AS aov,
        COUNT(DISTINCT customer_id) AS unique_customers,
        ROUND(SUM(discount) * 100.0 / NULLIF(SUM(total_amount + discount), 0), 2) AS discount_rate
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY year_month
)
SELECT
    year_month,
    total_orders,
    revenue,
    aov,
    unique_customers,
    discount_rate,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY year_month))
        / LAG(revenue) OVER (ORDER BY year_month) * 100, 2) AS revenue_growth_pct,
    ROUND((total_orders - LAG(total_orders) OVER (ORDER BY year_month))
        / LAG(total_orders) OVER (ORDER BY year_month) * 100, 2) AS order_growth_pct
FROM monthly_kpis
ORDER BY year_month;

-- 43. Top 10% Customers Revenue Contribution
WITH customer_value AS (
    SELECT
        customer_id,
        ROUND(SUM(total_amount), 2) AS lifetime_value,
        NTILE(10) OVER (ORDER BY SUM(total_amount) DESC) AS decile
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
)
SELECT
    CASE WHEN decile = 1 THEN 'Top 10%'
         WHEN decile <= 4 THEN 'Top 40%'
         ELSE 'Bottom 60%'
    END AS customer_group,
    COUNT(customer_id) AS customer_count,
    ROUND(SUM(lifetime_value), 2) AS total_revenue,
    ROUND(SUM(lifetime_value) * 100.0 / (SELECT SUM(lifetime_value) FROM customer_value), 2) AS revenue_share_pct
FROM customer_value
GROUP BY customer_group
ORDER BY revenue_share_pct DESC;

-- 44. Daily Active Users & Order Trends (Last 90 Days)
SELECT
    o.order_date,
    COUNT(DISTINCT o.customer_id) AS daily_active_users,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(o.total_amount), 2) AS revenue,
    ROUND(AVG(o.total_amount), 2) AS aov,
    ROUND(COUNT(DISTINCT o.order_id) * 1.0 / COUNT(DISTINCT o.customer_id), 2) AS orders_per_user
FROM orders o
WHERE o.order_status = 'Delivered'
  AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
GROUP BY o.order_date
ORDER BY o.order_date;

-- 45. Payment Method Adoption Trends (Monthly)
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS year_month,
    payment_method,
    COUNT(*) AS transaction_count,
    ROUND(SUM(total_amount), 2) AS transaction_value,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY DATE_FORMAT(order_date, '%Y-%m')), 2) AS usage_share_pct
FROM orders
WHERE order_status = 'Delivered'
GROUP BY year_month, payment_method
ORDER BY year_month, transaction_count DESC;

-- 46. Customer Retention Cohort Analysis
-- Tracks what fraction of each monthly acquisition cohort returns
-- in subsequent months.  month_offset = 0 is the signup month itself.
WITH first_order AS (
    SELECT
        customer_id,
        MIN(order_date) AS first_order_date,
        DATE_FORMAT(MIN(order_date), '%Y-%m-01') AS cohort_month
    FROM orders
    WHERE order_status IN ('Delivered', 'Refunded')
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        PERIOD_DIFF(
            DATE_FORMAT(o.order_date, '%Y%m'),
            DATE_FORMAT(f.first_order_date, '%Y%m')
        ) AS month_offset,
        COUNT(DISTINCT o.customer_id) AS active_customers
    FROM first_order f
    JOIN orders o ON f.customer_id = o.customer_id
        AND o.order_status IN ('Delivered', 'Refunded')
    GROUP BY f.cohort_month, month_offset
)
SELECT
    cohort_month,
    MAX(CASE WHEN month_offset = 0 THEN active_customers END) AS month_0,
    ROUND(MAX(CASE WHEN month_offset = 1 THEN active_customers END) * 100.0
        / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_customers END), 0), 1) AS month_1_retention_pct,
    ROUND(MAX(CASE WHEN month_offset = 2 THEN active_customers END) * 100.0
        / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_customers END), 0), 1) AS month_2_retention_pct,
    ROUND(MAX(CASE WHEN month_offset = 3 THEN active_customers END) * 100.0
        / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_customers END), 0), 1) AS month_3_retention_pct
FROM cohort_activity
WHERE cohort_month >= '2022-01-01'
GROUP BY cohort_month
ORDER BY cohort_month;

-- 47. Customer Lifetime Value Trend (Top 10% by Monthly Cohort)
-- Shows whether newly acquired customers are spending more or less over time.
-- Step 1: aggregate to customer-month level (no window functions in GROUP BY)
WITH customer_monthly AS (
    SELECT
        o.customer_id,
        DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
        SUM(o.total_amount) AS monthly_spend
    FROM orders o
    WHERE o.order_status = 'Delivered'
    GROUP BY o.customer_id, DATE_FORMAT(o.order_date, '%Y-%m')
),
-- Step 2: add acquisition month via window function
cohort_ltv AS (
    SELECT
        order_month,
        MIN(order_month) OVER(PARTITION BY customer_id) AS acquisition_month,
        customer_id,
        monthly_spend
    FROM customer_monthly
)
SELECT
    acquisition_month,
    COUNT(DISTINCT customer_id) AS acquired_customers,
    ROUND(AVG(monthly_spend), 2) AS avg_monthly_spend_per_customer,
    ROUND(SUM(monthly_spend), 2) AS total_cohort_revenue
FROM cohort_ltv
WHERE order_month = acquisition_month  -- only their first month's spend
  AND acquisition_month >= '2022-01'
GROUP BY acquisition_month
ORDER BY acquisition_month;

-- 48. Platform Economics Breakdown
-- Shows each component's share of the pre-discount total.
-- Discounts (negative) are converted to absolute values for percentage calculation.
WITH components AS (
    SELECT 'Food Value' AS component, SUM(order_amount) AS raw_value
    FROM orders WHERE order_status = 'Delivered'
    UNION ALL
    SELECT 'Delivery Fee', SUM(delivery_fee)
    FROM orders WHERE order_status = 'Delivered'
    UNION ALL
    SELECT 'Tax', SUM(tax)
    FROM orders WHERE order_status = 'Delivered'
    UNION ALL
    SELECT 'Platform Fee', SUM(platform_fee)
    FROM orders WHERE order_status = 'Delivered'
    UNION ALL
    SELECT 'Discounts Given', SUM(discount)
    FROM orders WHERE order_status = 'Delivered'
)
SELECT
    component,
    ROUND(raw_value, 2) AS total_value,
    ROUND(raw_value * 100.0 / NULLIF(SUM(ABS(raw_value)) OVER(), 0), 2) AS share_pct
FROM components;

-- 49. Surge Pricing Impact Analysis
SELECT
    CASE
        WHEN surge_multiplier = 1.00 THEN 'No Surge'
        WHEN surge_multiplier <= 1.20 THEN 'Low Surge (1.01-1.20)'
        WHEN surge_multiplier <= 1.35 THEN 'Medium Surge (1.21-1.35)'
        ELSE 'High Surge (1.36+)'
    END AS surge_bucket,
    COUNT(*) AS order_count,
    ROUND(SUM(total_amount), 2) AS revenue_including_surge,
    ROUND(SUM(total_amount / surge_multiplier), 2) AS revenue_without_surge,
    ROUND(SUM(total_amount) - SUM(total_amount / surge_multiplier), 2) AS surge_premium,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct
FROM orders
GROUP BY surge_bucket
ORDER BY MIN(surge_multiplier);

-- 50. Business Health Scorecard
SELECT
    'Total Revenue (All Time)' AS metric,
    ROUND(SUM(total_amount), 2) AS value,
    'INR' AS unit
FROM orders WHERE order_status = 'Delivered'
UNION ALL
SELECT 'Total Orders', COUNT(*), 'Orders'
FROM orders WHERE order_status = 'Delivered'
UNION ALL
SELECT 'Average Order Value', ROUND(AVG(total_amount), 2), 'INR'
FROM orders WHERE order_status = 'Delivered'
UNION ALL
SELECT 'Customer Retention Rate',
    ROUND(COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) * 100.0
        / NULLIF(COUNT(DISTINCT customer_id), 0), 2), '%'
FROM (SELECT customer_id, COUNT(*) AS order_count
      FROM orders WHERE order_status = 'Delivered' GROUP BY customer_id) sub
UNION ALL
SELECT 'On-Time Delivery Rate',
    ROUND(SUM(CASE WHEN is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2), '%'
FROM delivery_logs
UNION ALL
SELECT 'Avg Customer Rating', ROUND(AVG(customer_rating), 2), 'Stars'
FROM orders WHERE customer_rating IS NOT NULL
UNION ALL
SELECT 'Revenue Lost to Cancellations', ROUND(SUM(total_amount), 2), 'INR'
FROM orders WHERE order_status = 'Cancelled'
UNION ALL
SELECT 'Active Restaurants', COUNT(*), 'Count'
FROM restaurants WHERE is_active = 1
UNION ALL
SELECT 'Active Drivers', COUNT(*), 'Count'
FROM drivers WHERE is_active = 1;
