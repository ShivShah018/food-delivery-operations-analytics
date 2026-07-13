-- ============================================================
-- SwiftDash Operations Analytics — Database Schema
-- Platform: MySQL 8.0+
-- Description: Normalised star-schema for food-delivery analytics.
-- Normalisation choices:
--   * delivery_logs is a separate 1:1 table (not embedded in
--     orders) because operational data (weather, traffic) has
--     different update frequency than transactional data.
--   * customer_city / restaurant_city are denormalised in orders
--     to avoid frequent joins in city-level aggregations — a
--     deliberate performance trade-off for the analytics use case.
-- ============================================================

CREATE DATABASE IF NOT EXISTS swiftdash_analytics
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE swiftdash_analytics;

-- -----------------------------------------------------------
-- 1. Customers
-- -----------------------------------------------------------
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id     VARCHAR(20)     PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    age             INT             CHECK (age BETWEEN 16 AND 90),
    gender          ENUM('Male', 'Female', 'Other') DEFAULT 'Other',
    city            VARCHAR(50)     NOT NULL,
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),
    phone           VARCHAR(20),
    email           VARCHAR(100),
    signup_date     DATE,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 2. Restaurants
-- -----------------------------------------------------------
DROP TABLE IF EXISTS restaurants;
CREATE TABLE restaurants (
    restaurant_id       VARCHAR(20)     PRIMARY KEY,
    name                VARCHAR(150)    NOT NULL,
    cuisine_type        VARCHAR(50)     NOT NULL,
    city                VARCHAR(50)     NOT NULL,
    latitude            DECIMAL(9,6),
    longitude           DECIMAL(9,6),
    rating              DECIMAL(2,1)    CHECK (rating BETWEEN 1.0 AND 5.0),
    avg_cost_for_two    INT             CHECK (avg_cost_for_two >= 50),
    join_date           DATE,
    is_active           BOOLEAN         DEFAULT TRUE,
    preparation_time_mins INT           CHECK (preparation_time_mins BETWEEN 2 AND 60),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 3. Drivers
-- -----------------------------------------------------------
DROP TABLE IF EXISTS drivers;
CREATE TABLE drivers (
    driver_id       VARCHAR(20)     PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    age             INT             CHECK (age BETWEEN 18 AND 65),
    city            VARCHAR(50)     NOT NULL,
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),
    vehicle_type    ENUM('Bicycle', 'Motorcycle', 'Scooter', 'Car') DEFAULT 'Motorcycle',
    rating          DECIMAL(2,1)    CHECK (rating BETWEEN 1.0 AND 5.0),
    join_date       DATE,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 4. Orders (Central Fact Table)
-- -----------------------------------------------------------
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id            VARCHAR(20)     PRIMARY KEY,
    customer_id         VARCHAR(20)     NOT NULL,
    restaurant_id       VARCHAR(20)     NOT NULL,
    driver_id           VARCHAR(20),
    order_datetime      DATETIME        NOT NULL,
    order_date          DATE,
    order_hour         TINYINT         CHECK (order_hour BETWEEN 0 AND 23),
    weekday             VARCHAR(10),
    is_weekend          BOOLEAN         DEFAULT FALSE,
    order_amount        DECIMAL(10,2)   CHECK (order_amount >= 0),
    delivery_fee        DECIMAL(8,2)    DEFAULT 0,
    discount            DECIMAL(8,2)    DEFAULT 0,
    tax                 DECIMAL(8,2)    DEFAULT 0,
    platform_fee        DECIMAL(6,2)    DEFAULT 0,
    surge_multiplier    DECIMAL(3,2)    DEFAULT 1.00,
    total_amount        DECIMAL(10,2)   CHECK (total_amount >= 0),
    payment_method      ENUM('UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wallet', 'COD'),
    order_status        ENUM('Delivered', 'Cancelled', 'Refunded') DEFAULT 'Delivered',
    customer_city       VARCHAR(50),
    restaurant_city     VARCHAR(50),
    customer_rating     TINYINT         CHECK (customer_rating BETWEEN 1 AND 5 OR customer_rating IS NULL),

    FOREIGN KEY (customer_id)   REFERENCES customers(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (driver_id)     REFERENCES drivers(driver_id) ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_order_date (order_date),
    INDEX idx_customer (customer_id),
    INDEX idx_restaurant (restaurant_id),
    INDEX idx_status (order_status),
    INDEX idx_payment (payment_method)
);

-- -----------------------------------------------------------
-- 5. Order Items
-- -----------------------------------------------------------
DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    order_item_id   INT             PRIMARY KEY AUTO_INCREMENT,
    order_id        VARCHAR(20)     NOT NULL,
    item_name       VARCHAR(100)    NOT NULL,
    category        VARCHAR(50),
    quantity        INT             CHECK (quantity > 0),
    unit_price      DECIMAL(10,2)   CHECK (unit_price > 0),
    line_total      DECIMAL(10,2)   CHECK (line_total >= 0),

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_order (order_id),
    INDEX idx_category (category)
);

-- -----------------------------------------------------------
-- 6. Delivery Logs
-- -----------------------------------------------------------
DROP TABLE IF EXISTS delivery_logs;
CREATE TABLE delivery_logs (
    delivery_id         VARCHAR(30)     PRIMARY KEY,
    order_id            VARCHAR(20)     NOT NULL UNIQUE,
    driver_id           VARCHAR(20)     NOT NULL,
    pickup_datetime     DATETIME,
    drop_datetime       DATETIME,
    distance_km         DECIMAL(8,2)    CHECK (distance_km > 0),
    travel_time_mins    INT             CHECK (travel_time_mins > 0),
    traffic_condition   ENUM('Low', 'Moderate', 'High', 'Gridlock'),
    weather_condition   ENUM('Clear', 'Cloudy', 'Light Rain', 'Heavy Rain', 'Foggy'),
    is_on_time          BOOLEAN         DEFAULT TRUE,

    FOREIGN KEY (order_id)  REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_driver (driver_id),
    INDEX idx_on_time (is_on_time)
);

-- ============================================================
-- End of Schema
-- ============================================================
