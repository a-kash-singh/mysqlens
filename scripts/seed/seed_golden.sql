-- MySQLens Golden Dataset Scenarios
-- Creates test tables with specific characteristics for LLM benchmark validation

CREATE DATABASE IF NOT EXISTS mysqlens_golden;
USE mysqlens_golden;

-- =============================================================================
-- Scenario A: The "Slam Dunk" (1M row table without index on user_id)
-- Expected: LLM should suggest CREATE INDEX on user_id
-- =============================================================================

DROP TABLE IF EXISTS golden_orders;
CREATE TABLE golden_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- NO INDEX on user_id intentionally
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Fast seeding using stored procedure
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS seed_golden_orders()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE batch_size INT DEFAULT 10000;
    
    WHILE i < 1000000 DO
        INSERT INTO golden_orders (user_id, amount, created_at)
        SELECT 
            FLOOR(1 + RAND() * 100000),
            ROUND(RAND() * 500, 2),
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY)
        FROM (
            SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 AS n
            FROM 
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d
            LIMIT 10000
        ) nums;
        
        SET i = i + batch_size;
        
        IF i % 100000 = 0 THEN
            SELECT CONCAT('Inserted ', i, ' rows into golden_orders') AS progress;
        END IF;
    END WHILE;
END//
DELIMITER ;

-- Seed the orders (comment out if takes too long for testing)
-- CALL seed_golden_orders();

-- Alternative: Seed smaller dataset for quick testing
INSERT INTO golden_orders (user_id, amount, created_at)
SELECT 
    FLOOR(1 + RAND() * 10000),
    ROUND(RAND() * 500, 2),
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY)
FROM (
    SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 + e.N * 10000 AS n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) e
    LIMIT 100000
) nums;

-- =============================================================================
-- Scenario B: The "Trap" (INSERT statement - should NOT suggest index)
-- Expected: LLM should return ADVISORY, not INDEX
-- =============================================================================
-- No additional table needed - uses golden_orders
-- Test query: INSERT INTO golden_orders (user_id, amount) VALUES (123, 45.67)

-- =============================================================================
-- Scenario C: The "Tiny Table" (15 rows - index would be overkill)
-- Expected: LLM should return ADVISORY, not INDEX
-- =============================================================================

DROP TABLE IF EXISTS golden_user_roles;
CREATE TABLE golden_user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT
) ENGINE=InnoDB;

INSERT INTO golden_user_roles (code, description) VALUES
('ADMIN', 'System Administrator'),
('USER', 'Regular User'),
('GUEST', 'Guest User'),
('EDITOR', 'Content Editor'),
('MODERATOR', 'Community Moderator'),
('SUPPORT', 'Customer Support'),
('BILLING', 'Billing Manager'),
('MANAGER', 'General Manager'),
('VIEWER', 'Read-only Viewer'),
('ANALYST', 'Data Analyst'),
('DEVELOPER', 'System Developer'),
('MARKETER', 'Marketing Specialist'),
('SALES', 'Sales Representative'),
('HR', 'Human Resources'),
('SECURITY', 'Security Auditor');

-- =============================================================================
-- Scenario D: Function on Column (YEAR(created_at) prevents index usage)
-- Expected: LLM should suggest REWRITE with date range
-- =============================================================================

DROP TABLE IF EXISTS golden_users;
CREATE TABLE golden_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

INSERT INTO golden_users (username, email, created_at)
SELECT 
    CONCAT('user_', n),
    CONCAT('user_', n, '@example.com'),
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 1825) DAY)  -- Random date in last 5 years
FROM (
    SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 AS n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d
    LIMIT 10000
) nums;

-- =============================================================================
-- Scenario E: Join Bottleneck (Missing index on FK column)
-- Expected: LLM should suggest INDEX on product_reviews.product_id
-- =============================================================================

DROP TABLE IF EXISTS golden_product_reviews;
DROP TABLE IF EXISTS golden_products;

CREATE TABLE golden_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2)
) ENGINE=InnoDB;

CREATE TABLE golden_product_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,  -- NO INDEX intentionally
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    -- NO FOREIGN KEY or INDEX on product_id
) ENGINE=InnoDB;

-- Seed products
INSERT INTO golden_products (name, category, price)
SELECT 
    CONCAT('Product ', n),
    ELT(FLOOR(1 + RAND() * 4), 'Electronics', 'Books', 'Clothing', 'Home'),
    ROUND(RAND() * 1000, 2)
FROM (
    SELECT a.N + b.N * 10 + c.N * 100 AS n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c
    LIMIT 1000
) nums;

-- Seed reviews
INSERT INTO golden_product_reviews (product_id, rating, comment, created_at)
SELECT 
    FLOOR(1 + RAND() * 1000),
    FLOOR(1 + RAND() * 5),
    CONCAT('Review comment for product ', FLOOR(1 + RAND() * 1000)),
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 180) DAY)
FROM (
    SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 + e.N * 10000 AS n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) e
    LIMIT 100000
) nums;

-- =============================================================================
-- Scenario F: Large Aggregation (GROUP BY on large table)
-- Expected: ADVISORY or INDEX depending on context
-- =============================================================================

DROP TABLE IF EXISTS golden_events;
CREATE TABLE golden_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(20) NOT NULL,
    user_id INT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
    -- NO INDEX on event_type intentionally
) ENGINE=InnoDB;

INSERT INTO golden_events (event_type, user_id, metadata, created_at)
SELECT 
    ELT(FLOOR(1 + RAND() * 5), 'click', 'view', 'purchase', 'login', 'logout'),
    FLOOR(1 + RAND() * 10000),
    JSON_OBJECT('source', 'mobile', 'version', '1.2.3'),
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
FROM (
    SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 + e.N * 10000 AS n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) e
    LIMIT 500000
) nums;

-- =============================================================================
-- Benchmark Results Storage
-- =============================================================================

DROP TABLE IF EXISTS golden_benchmark_results;
CREATE TABLE golden_benchmark_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id VARCHAR(10) NOT NULL,
    query_text TEXT NOT NULL,
    prompt TEXT,
    raw_response TEXT,
    actual_category VARCHAR(50),
    expected_category VARCHAR(50),
    actual_sql TEXT,
    alignment_score FLOAT,
    duration_ms INT,
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scenario (scenario_id),
    INDEX idx_alignment (alignment_score),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- Update table statistics
-- =============================================================================

ANALYZE TABLE golden_orders;
ANALYZE TABLE golden_user_roles;
ANALYZE TABLE golden_users;
ANALYZE TABLE golden_products;
ANALYZE TABLE golden_product_reviews;
ANALYZE TABLE golden_events;

-- =============================================================================
-- Summary
-- =============================================================================

SELECT 'Golden dataset created successfully!' AS status;
SELECT 
    'golden_orders' AS table_name, (SELECT COUNT(*) FROM golden_orders) AS row_count
UNION ALL SELECT 'golden_user_roles', (SELECT COUNT(*) FROM golden_user_roles)
UNION ALL SELECT 'golden_users', (SELECT COUNT(*) FROM golden_users)
UNION ALL SELECT 'golden_products', (SELECT COUNT(*) FROM golden_products)
UNION ALL SELECT 'golden_product_reviews', (SELECT COUNT(*) FROM golden_product_reviews)
UNION ALL SELECT 'golden_events', (SELECT COUNT(*) FROM golden_events);
