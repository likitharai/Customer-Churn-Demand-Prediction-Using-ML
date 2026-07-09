-- Executive Dashboard KPI Queries

-- 1. Executive KPI summary (single row)
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) AS total_churned,
    ROUND(100.0 * SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue,
    ROUND(SUM(CASE WHEN churn = 'Yes' THEN monthly_charges ELSE 0 END), 2) AS revenue_at_risk,
    ROUND(AVG(tenure), 1) AS avg_customer_tenure
FROM customers;

-- 2. Monthly churn trend (if created_at is populated)
SELECT
    TO_CHAR(created_at, 'YYYY-MM') AS month,
    COUNT(*) AS new_customers,
    SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) AS churned
FROM customers
GROUP BY month
ORDER BY month;

-- 3. Risk level distribution from predictions table
SELECT
    risk_level,
    COUNT(*) AS customer_count,
    ROUND(AVG(probability) * 100, 2) AS avg_churn_probability_pct
FROM predictions
GROUP BY risk_level
ORDER BY avg_churn_probability_pct DESC;
