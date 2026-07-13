-- ============================================================
-- CUSTOMER ANALYSIS QUERIES
-- Segmentation, retention, lifetime value, demographics
-- ============================================================

-- 11. Customer Lifetime Value (Top 20)
SELECT
    c.customer_id,
    c.name,
    c.city,
    c.gender,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS lifetime_value,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(AVG(o.discount), 2) AS avg_discount,
    MAX(o.order_date) AS last_order_date,
    DATEDIFF(CURDATE(), MAX(o.order_date)) AS days_since_last_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Delivered'
GROUP BY c.customer_id, c.name, c.city, c.gender
ORDER BY lifetime_value DESC
LIMIT 20;

-- 12. Customer Segmentation (RFM-based)
WITH customer_rfm AS (
    SELECT
        c.customer_id,
        DATEDIFF(CURDATE(), MAX(o.order_date)) AS recency_days,
        COUNT(o.order_id) AS frequency,
        ROUND(SUM(o.total_amount), 2) AS monetary
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
        AND o.order_status = 'Delivered'
    GROUP BY c.customer_id
)
SELECT
    CASE
        WHEN recency_days <= 30 AND frequency >= 15 AND monetary >= 10000 THEN 'Platinum'
        WHEN recency_days <= 60 AND frequency >= 8 AND monetary >= 5000 THEN 'Gold'
        WHEN recency_days <= 90 THEN 'Silver'
        WHEN recency_days <= 180 THEN 'At Risk'
        WHEN frequency = 0 THEN 'New'
        ELSE 'Churned'
    END AS customer_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(monetary), 2) AS avg_lifetime_value,
    ROUND(AVG(frequency), 1) AS avg_orders,
    ROUND(AVG(recency_days), 0) AS avg_recency_days
FROM customer_rfm
GROUP BY customer_segment
ORDER BY avg_lifetime_value DESC;

-- 13. Repeat Customer Rate (Monthly)
WITH monthly_orders AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS year_month,
        customer_id,
        COUNT(order_id) AS orders_count
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY year_month, customer_id
),
monthly_metrics AS (
    SELECT
        year_month,
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT CASE WHEN orders_count > 1 THEN customer_id END) AS repeat_customers
    FROM monthly_orders
    GROUP BY year_month
)
SELECT
    year_month,
    total_customers,
    repeat_customers,
    ROUND(repeat_customers * 100.0 / total_customers, 2) AS repeat_customer_rate_pct
FROM monthly_metrics
ORDER BY year_month;

-- 14. Customer Acquisition Trend (First-time orderers per month)
WITH first_orders AS (
    SELECT
        customer_id,
        MIN(order_date) AS first_order_date
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
)
SELECT
    DATE_FORMAT(first_order_date, '%Y-%m') AS acquisition_month,
    COUNT(customer_id) AS new_customers
FROM first_orders
GROUP BY acquisition_month
ORDER BY acquisition_month;

-- 15. Age Group Analysis
SELECT
    CASE
        WHEN c.age BETWEEN 18 AND 24 THEN '18-24'
        WHEN c.age BETWEEN 25 AND 34 THEN '25-34'
        WHEN c.age BETWEEN 35 AND 44 THEN '35-44'
        WHEN c.age BETWEEN 45 AND 54 THEN '45-54'
        ELSE '55+'
    END AS age_group,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
    AND o.order_status = 'Delivered'
GROUP BY age_group
ORDER BY age_group;

-- 16. Gender-Based Spending Patterns
SELECT
    c.gender,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer,
    ROUND(AVG(o.discount), 2) AS avg_discount_availed
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
    AND o.order_status = 'Delivered'
GROUP BY c.gender
ORDER BY total_revenue DESC;

-- 17. Top 10 Cities by Customer Base
SELECT
    city,
    COUNT(DISTINCT customer_id) AS customer_count,
    COUNT(DISTINCT CASE WHEN is_active = 1 THEN customer_id END) AS active_customers,
    ROUND(COUNT(DISTINCT CASE WHEN is_active = 1 THEN customer_id END) * 100.0
        / COUNT(DISTINCT customer_id), 2) AS active_rate_pct
FROM customers
GROUP BY city
ORDER BY customer_count DESC
LIMIT 10;

-- 18. Customers with Highest Discount Usage
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.discount), 2) AS total_discount_received,
    ROUND(AVG(o.discount), 2) AS avg_discount_per_order,
    ROUND(AVG(o.discount) * 100.0 / NULLIF(AVG(o.total_amount + o.discount), 0), 2) AS avg_discount_rate_pct
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY c.customer_id, c.name
HAVING total_orders >= 5
ORDER BY avg_discount_rate_pct DESC
LIMIT 15;

-- 19. Customer Order Frequency Distribution
WITH order_counts AS (
    SELECT
        customer_id,
        COUNT(order_id) AS total_orders
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN total_orders = 1 THEN '1 Order'
        WHEN total_orders BETWEEN 2 AND 5 THEN '2-5 Orders'
        WHEN total_orders BETWEEN 6 AND 15 THEN '6-15 Orders'
        WHEN total_orders BETWEEN 16 AND 30 THEN '16-30 Orders'
        ELSE '30+ Orders'
    END AS order_frequency_bucket,
    COUNT(customer_id) AS customer_count,
    ROUND(COUNT(customer_id) * 100.0 / SUM(COUNT(customer_id)) OVER(), 2) AS pct_of_customers
FROM order_counts
GROUP BY order_frequency_bucket
ORDER BY MIN(total_orders);

-- 20. Customer Preferred Payment Method
SELECT
    c.customer_id,
    c.name,
    o.payment_method,
    COUNT(*) AS times_used,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY c.customer_id), 1) AS usage_pct
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY c.customer_id, c.name, o.payment_method
HAVING COUNT(*) >= 3 AND usage_pct > 50
ORDER BY c.customer_id, times_used DESC;
