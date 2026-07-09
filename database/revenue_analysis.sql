-- Revenue Risk Analysis Queries

-- 1. Total monthly revenue at risk from churned customers
SELECT
    ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue,
    ROUND(SUM(CASE WHEN churn = 'Yes' THEN monthly_charges ELSE 0 END), 2) AS revenue_lost_to_churn,
    ROUND(100.0 * SUM(CASE WHEN churn = 'Yes' THEN monthly_charges ELSE 0 END) / SUM(monthly_charges), 2) AS revenue_loss_pct
FROM customers;

-- 2. Revenue at risk by contract type
SELECT
    contract,
    ROUND(SUM(monthly_charges), 2) AS total_revenue,
    ROUND(SUM(CASE WHEN churn = 'Yes' THEN monthly_charges ELSE 0 END), 2) AS revenue_at_risk,
    COUNT(CASE WHEN churn = 'Yes' THEN 1 END) AS churned_customers
FROM customers
GROUP BY contract
ORDER BY revenue_at_risk DESC;

-- 3. Revenue at risk by internet service
SELECT
    internet_service,
    ROUND(SUM(CASE WHEN churn = 'Yes' THEN monthly_charges ELSE 0 END), 2) AS revenue_at_risk,
    COUNT(CASE WHEN churn = 'Yes' THEN 1 END) AS churned_count
FROM customers
GROUP BY internet_service
ORDER BY revenue_at_risk DESC;

-- 4. Average charges comparison: churned vs retained
SELECT
    churn,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly,
    ROUND(AVG(total_charges), 2) AS avg_total,
    ROUND(AVG(tenure), 1) AS avg_tenure
FROM customers
GROUP BY churn;
