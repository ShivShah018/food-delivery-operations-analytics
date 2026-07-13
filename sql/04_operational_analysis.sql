-- ============================================================
-- OPERATIONAL & DELIVERY ANALYSIS QUERIES
-- Delivery performance, driver metrics, restaurant operations
-- ============================================================

-- 21. Average Delivery Time by Hour
SELECT
    o.order_hour,
    COUNT(d.delivery_id) AS deliveries,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_travel_time_mins,
    ROUND(AVG(d.distance_km), 2) AS avg_distance_km,
    ROUND(SUM(CASE WHEN d.is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate_pct
FROM delivery_logs d
JOIN orders o ON d.order_id = o.order_id
GROUP BY o.order_hour
ORDER BY o.order_hour;

-- 22. Delivery Performance by Traffic Condition
SELECT
    d.traffic_condition,
    COUNT(*) AS delivery_count,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_travel_time,
    ROUND(AVG(d.distance_km), 2) AS avg_distance,
    ROUND(SUM(CASE WHEN d.is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate_pct,
    ROUND(AVG(d.travel_time_mins / NULLIF(d.distance_km, 0)), 2) AS mins_per_km
FROM delivery_logs d
GROUP BY d.traffic_condition
ORDER BY on_time_rate_pct;

-- 23. Driver Efficiency Ranking
SELECT
    dr.driver_id,
    dr.name,
    dr.city,
    dr.vehicle_type,
    COUNT(d.delivery_id) AS total_deliveries,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_delivery_time,
    ROUND(AVG(d.distance_km), 2) AS avg_distance,
    ROUND(SUM(CASE WHEN d.is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate_pct,
    dr.rating AS driver_rating
FROM drivers dr
JOIN delivery_logs d ON dr.driver_id = d.driver_id
GROUP BY dr.driver_id, dr.name, dr.city, dr.vehicle_type, dr.rating
HAVING total_deliveries >= 50
ORDER BY on_time_rate_pct DESC, avg_delivery_time ASC
LIMIT 20;

-- 24. Vehicle Type Performance Comparison
SELECT
    dr.vehicle_type,
    COUNT(DISTINCT dr.driver_id) AS driver_count,
    COUNT(d.delivery_id) AS total_deliveries,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_travel_time,
    ROUND(AVG(d.distance_km), 2) AS avg_distance,
    ROUND(SUM(CASE WHEN d.is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate_pct,
    ROUND(AVG(dr.rating), 2) AS avg_driver_rating
FROM drivers dr
JOIN delivery_logs d ON dr.driver_id = d.driver_id
GROUP BY dr.vehicle_type
ORDER BY on_time_rate_pct DESC;

-- 25. Weather Impact on Delivery
SELECT
    d.weather_condition,
    COUNT(*) AS delivery_count,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_travel_time,
    ROUND(SUM(CASE WHEN d.is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate_pct,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(AVG(o.discount), 2) AS avg_discount
FROM delivery_logs d
JOIN orders o ON d.order_id = o.order_id
GROUP BY d.weather_condition
ORDER BY on_time_rate_pct;

-- 26. Restaurant Preparation Time vs. Delivery Success
SELECT
    r.restaurant_id,
    r.name,
    r.cuisine_type,
    r.preparation_time_mins,
    COUNT(o.order_id) AS total_orders,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_delivery_time,
    ROUND(AVG(o.customer_rating), 2) AS avg_customer_rating,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct
FROM restaurants r
LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
LEFT JOIN delivery_logs d ON o.order_id = d.order_id
GROUP BY r.restaurant_id, r.name, r.cuisine_type, r.preparation_time_mins
ORDER BY cancellation_rate_pct DESC
LIMIT 20;

-- 27. Peak Order Hours Analysis
SELECT
    o.order_hour,
    COUNT(*) AS order_volume,
    ROUND(SUM(o.total_amount), 2) AS revenue,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_delivery_time,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct
FROM orders o
LEFT JOIN delivery_logs d ON o.order_id = d.order_id
GROUP BY o.order_hour
ORDER BY order_volume DESC;

-- 28. City-Wise Operational Metrics
SELECT
    o.restaurant_city AS city,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT r.restaurant_id) AS active_restaurants,
    COUNT(DISTINCT d.driver_id) AS active_drivers,
    ROUND(AVG(d.travel_time_mins), 1) AS avg_delivery_time_mins,
    ROUND(SUM(CASE WHEN d.is_on_time = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(d.delivery_id), 0), 2) AS on_time_rate_pct,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct
FROM orders o
LEFT JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN delivery_logs d ON o.order_id = d.order_id
GROUP BY o.restaurant_city
ORDER BY total_orders DESC;

-- 29. Orders with Long Delivery Times (Outliers)
SELECT
    o.order_id,
    o.order_datetime,
    d.pickup_datetime,
    d.drop_datetime,
    d.travel_time_mins,
    d.distance_km,
    d.traffic_condition,
    d.weather_condition,
    o.total_amount,
    o.customer_rating
FROM delivery_logs d
JOIN orders o ON d.order_id = o.order_id
WHERE d.travel_time_mins > 60
ORDER BY d.travel_time_mins DESC
LIMIT 25;

-- 30. Refund Analysis
-- Uses a CTE to avoid correlated-subquery scoping issues.
WITH monthly_totals AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS year_month,
        COUNT(*) AS total_orders
    FROM orders
    WHERE order_status IN ('Delivered', 'Refunded')
    GROUP BY year_month
)
SELECT
    DATE_FORMAT(o.order_date, '%Y-%m') AS year_month,
    COUNT(*) AS refund_count,
    ROUND(SUM(o.total_amount), 2) AS refund_amount,
    ROUND(AVG(o.customer_rating), 2) AS avg_rating,
    ROUND(COUNT(*) * 100.0 / NULLIF(MAX(mt.total_orders), 0), 3) AS refund_rate_pct
FROM orders o
JOIN monthly_totals mt ON DATE_FORMAT(o.order_date, '%Y-%m') = mt.year_month
WHERE o.order_status = 'Refunded'
GROUP BY year_month
ORDER BY year_month;
