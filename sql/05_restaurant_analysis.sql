-- ============================================================
-- RESTAURANT & PRODUCT ANALYSIS QUERIES
-- Performance, popularity, cuisine trends
-- ============================================================

-- 31. Top Performing Restaurants by Revenue
SELECT
    r.restaurant_id,
    r.name,
    r.cuisine_type,
    r.city,
    r.rating AS restaurant_rating,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(AVG(o.customer_rating), 2) AS avg_customer_rating,
    ROUND(SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.customer_id), 0), 2) AS revenue_per_customer
FROM restaurants r
JOIN orders o ON r.restaurant_id = o.restaurant_id
WHERE o.order_status = 'Delivered'
GROUP BY r.restaurant_id, r.name, r.cuisine_type, r.city, r.rating
ORDER BY total_revenue DESC
LIMIT 20;

-- 32. Cuisine Performance Dashboard
SELECT
    r.cuisine_type,
    COUNT(DISTINCT r.restaurant_id) AS restaurant_count,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(AVG(o.customer_rating), 2) AS avg_customer_rating,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(AVG(r.avg_cost_for_two), 0) AS avg_cost_for_two
FROM restaurants r
LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
GROUP BY r.cuisine_type
ORDER BY total_revenue DESC;

-- 33. Most Popular Items (by Order Frequency)
SELECT
    oi.item_name,
    oi.category AS cuisine_type,
    COUNT(DISTINCT oi.order_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity_sold,
    ROUND(SUM(oi.line_total), 2) AS total_revenue,
    ROUND(AVG(oi.unit_price), 2) AS avg_unit_price
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Delivered'
GROUP BY oi.item_name, oi.category
ORDER BY times_ordered DESC
LIMIT 25;

-- 34. Restaurant Average Rating vs. Order Volume
-- Per-restaurant metrics computed first, then averaged by rating bucket.
WITH restaurant_perf AS (
    SELECT
        r.rating,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(o.total_amount), 2) AS revenue
    FROM restaurants r
    JOIN orders o ON r.restaurant_id = o.restaurant_id
    WHERE o.order_status = 'Delivered'
    GROUP BY r.restaurant_id, r.rating
)
SELECT
    rating AS restaurant_rating_bucket,
    COUNT(*) AS restaurant_count,
    ROUND(AVG(orders), 0) AS avg_orders_per_restaurant,
    ROUND(AVG(revenue), 0) AS avg_revenue_per_restaurant
FROM restaurant_perf
GROUP BY rating
ORDER BY rating DESC;

-- 35. Restaurants with Highest Cancellation Rates
SELECT
    r.restaurant_id,
    r.name,
    r.cuisine_type,
    r.city,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(AVG(o.customer_rating), 2) AS avg_rating,
    r.preparation_time_mins,
    r.rating
FROM restaurants r
JOIN orders o ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.name, r.cuisine_type, r.city, r.preparation_time_mins, r.rating
HAVING COUNT(o.order_id) >= 30
ORDER BY cancellation_rate_pct DESC
LIMIT 15;

-- 36. Cross-Selling Analysis (Items frequently bought together)
SELECT
    a.item_name AS item_1,
    b.item_name AS item_2,
    COUNT(DISTINCT a.order_id) AS times_bought_together,
    ROUND(COUNT(DISTINCT a.order_id) * 100.0 / (
        SELECT COUNT(DISTINCT order_id) FROM order_items WHERE item_name = a.item_name
    ), 2) AS affinity_score_pct
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.item_name < b.item_name
JOIN orders o ON a.order_id = o.order_id AND o.order_status = 'Delivered'
GROUP BY a.item_name, b.item_name
HAVING times_bought_together >= 50
ORDER BY times_bought_together DESC
LIMIT 20;

-- 37. Monthly Active Restaurants Trend
SELECT
    DATE_FORMAT(o.order_date, '%Y-%m') AS year_month,
    COUNT(DISTINCT o.restaurant_id) AS active_restaurants,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT o.restaurant_id), 2) AS revenue_per_restaurant
FROM orders o
WHERE o.order_status = 'Delivered'
GROUP BY year_month
ORDER BY year_month;

-- 38. New Restaurant Onboarding vs. Performance
-- Per-restaurant metrics computed first, then averaged by join year.
WITH restaurant_perf AS (
    SELECT
        r.restaurant_id,
        r.join_date,
        COUNT(o.order_id) AS orders,
        ROUND(SUM(o.total_amount), 2) AS revenue,
        ROUND(AVG(o.customer_rating), 2) AS avg_customer_rating
    FROM restaurants r
    LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id AND o.order_status = 'Delivered'
    GROUP BY r.restaurant_id
)
SELECT
    DATE_FORMAT(join_date, '%Y') AS join_year,
    COUNT(*) AS restaurants_onboarded,
    ROUND(AVG(orders), 0) AS avg_orders_per_restaurant,
    ROUND(AVG(revenue), 0) AS avg_revenue_per_restaurant,
    ROUND(AVG(avg_customer_rating), 2) AS avg_customer_rating
FROM restaurant_perf
GROUP BY join_year
ORDER BY join_year;

-- 39. Cuisine Type Popularity by City
SELECT
    o.restaurant_city AS city,
    r.cuisine_type,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.total_amount), 2) AS revenue,
    ROW_NUMBER() OVER(PARTITION BY o.restaurant_city ORDER BY COUNT(DISTINCT o.order_id) DESC) AS rank_in_city
FROM orders o
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
WHERE o.order_status = 'Delivered'
GROUP BY o.restaurant_city, r.cuisine_type
HAVING rank_in_city <= 3
ORDER BY city, rank_in_city;

-- 40. Revenue Concentration (Top 20% restaurants contribution)
WITH restaurant_revenue AS (
    SELECT
        r.restaurant_id,
        r.name,
        ROUND(SUM(o.total_amount), 2) AS revenue,
        NTILE(5) OVER (ORDER BY SUM(o.total_amount) DESC) AS quintile
    FROM restaurants r
    JOIN orders o ON r.restaurant_id = o.restaurant_id
    WHERE o.order_status = 'Delivered'
    GROUP BY r.restaurant_id, r.name
)
SELECT
    CONCAT('Q', quintile) AS revenue_quintile,
    COUNT(*) AS restaurant_count,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM restaurant_revenue), 2) AS revenue_share_pct,
    ROUND(AVG(revenue), 2) AS avg_revenue_per_restaurant
FROM restaurant_revenue
GROUP BY quintile
ORDER BY quintile;
