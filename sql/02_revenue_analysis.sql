-- ============================================================
-- REVENUE ANALYSIS QUERIES
-- Analysis of revenue streams, trends, and profitability
--
-- REVENUE CONVENTION: Net revenue — only 'Delivered' orders
-- count.  Refunded orders are excluded from all revenue figures
-- and tracked separately in the refund analysis query (Q30).
-- ============================================================

-- 1. Daily Revenue Trend
SELECT
    order_date,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE order_status = 'Delivered'
GROUP BY order_date
ORDER BY order_date;

-- 2. Monthly Revenue with Growth Rate
WITH monthly_rev AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS year_month,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY year_month
)
SELECT
    year_month,
    revenue,
    LAG(revenue) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY year_month))
        / LAG(revenue) OVER (ORDER BY year_month) * 100, 2
    ) AS mom_growth_pct
FROM monthly_rev
ORDER BY year_month;

-- 3. Revenue Breakdown by Payment Method
SELECT
    payment_method,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    ROUND(SUM(total_amount) * 100.0 / SUM(SUM(total_amount)) OVER(), 2) AS revenue_share_pct
FROM orders
WHERE order_status = 'Delivered'
GROUP BY payment_method
ORDER BY total_revenue DESC;

-- 4. Revenue by City
SELECT
    restaurant_city AS city,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(SUM(order_amount), 2) AS food_revenue,
    ROUND(SUM(delivery_fee), 2) AS delivery_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE order_status = 'Delivered'
GROUP BY restaurant_city
ORDER BY total_revenue DESC;

-- 5. Hourly Revenue Distribution
SELECT
    order_hour,
    COUNT(*) AS order_count,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE order_status = 'Delivered'
GROUP BY order_hour
ORDER BY order_hour;

-- 6. Revenue Contribution by Customer Segment
WITH customer_revenue AS (
    SELECT
        c.customer_id,
        CASE
            WHEN COUNT(o.order_id) >= 25 AND SUM(o.total_amount) >= 15000 THEN 'Platinum'
            WHEN COUNT(o.order_id) >= 10 AND SUM(o.total_amount) >= 5000 THEN 'Gold'
            WHEN MAX(o.order_date) >= DATE_SUB(CURDATE(), INTERVAL 90 DAY) THEN 'Silver'
            WHEN MAX(o.order_date) >= DATE_SUB(CURDATE(), INTERVAL 180 DAY) THEN 'At Risk'
            ELSE 'Churned'
        END AS segment,
        ROUND(SUM(o.total_amount), 2) AS lifetime_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'Delivered'
    GROUP BY c.customer_id
)
SELECT
    segment,
    COUNT(customer_id) AS customer_count,
    ROUND(SUM(lifetime_value), 2) AS total_revenue,
    ROUND(SUM(lifetime_value) * 100.0 / SUM(SUM(lifetime_value)) OVER(), 2) AS revenue_share_pct,
    ROUND(AVG(lifetime_value), 2) AS avg_customer_value
FROM customer_revenue
GROUP BY segment
ORDER BY total_revenue DESC;

-- 7. Revenue Lost to Cancellations
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS year_month,
    COUNT(*) AS cancelled_orders,
    ROUND(SUM(order_amount), 2) AS lost_food_revenue,
    ROUND(SUM(delivery_fee + platform_fee), 2) AS lost_fees,
    ROUND(SUM(order_amount + delivery_fee + platform_fee), 2) AS total_loss
FROM orders
WHERE order_status = 'Cancelled'
GROUP BY year_month
ORDER BY year_month;

-- 8. Discount Impact on Revenue
SELECT
    CASE
        WHEN discount = 0 THEN 'No Discount'
        WHEN discount < 50 THEN 'Small (1-49)'
        WHEN discount < 150 THEN 'Medium (50-149)'
        ELSE 'Large (150+)'
    END AS discount_bucket,
    COUNT(*) AS order_count,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(SUM(discount), 2) AS total_discount_given,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    ROUND(SUM(discount) * 100.0 / NULLIF(SUM(total_amount + discount), 0), 2) AS discount_rate_pct
FROM orders
WHERE order_status = 'Delivered'
GROUP BY discount_bucket
ORDER BY total_revenue DESC;

-- 9. Weekday vs Weekend Revenue Comparison
SELECT
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    ROUND(SUM(total_amount) / COUNT(DISTINCT DATE(order_date)), 2) AS revenue_per_day
FROM orders
WHERE order_status = 'Delivered'
GROUP BY day_type;

-- 10. Revenue by Cuisine Type
SELECT
    r.cuisine_type,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(SUM(o.total_amount) * 100.0 / SUM(SUM(o.total_amount)) OVER(), 2) AS revenue_share_pct,
    COUNT(DISTINCT r.restaurant_id) AS restaurant_count
FROM orders o
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
WHERE o.order_status = 'Delivered'
GROUP BY r.cuisine_type
ORDER BY total_revenue DESC;
