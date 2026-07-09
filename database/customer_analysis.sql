-- Customer Segmentation & Behavioral Analysis

-- 1. Customer demographics breakdown
SELECT
    gender,
    COUNT(*) AS total,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months
FROM customers
GROUP BY gender;

-- 2. Service adoption rates
SELECT
    ROUND(100.0 * SUM(CASE WHEN phone_service = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS phone_pct,
    ROUND(100.0 * SUM(CASE WHEN online_security = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS security_pct,
    ROUND(100.0 * SUM(CASE WHEN tech_support = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS tech_support_pct,
    ROUND(100.0 * SUM(CASE WHEN streaming_tv = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1) AS streaming_tv_pct
FROM customers;

-- 3. High-value customers (top 20% by monthly charges)
SELECT
    customer_id, gender, tenure, monthly_charges, total_charges, contract, churn
FROM customers
WHERE monthly_charges >= (SELECT PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY monthly_charges) FROM customers)
ORDER BY monthly_charges DESC;

-- 4. Customers with no add-on services (high churn risk)
SELECT
    customer_id, tenure, monthly_charges, contract, churn
FROM customers
WHERE online_security = 'No'
  AND tech_support = 'No'
  AND online_backup = 'No'
ORDER BY tenure ASC;
