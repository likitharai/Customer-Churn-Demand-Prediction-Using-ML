-- Stored Procedures & Views

-- View: high risk customers
CREATE OR REPLACE VIEW high_risk_customers AS
SELECT
    c.customer_id,
    c.gender,
    c.tenure,
    c.contract,
    c.monthly_charges,
    p.probability,
    p.risk_level,
    p.predicted_at
FROM customers c
JOIN predictions p ON c.customer_id = p.customer_id
WHERE p.risk_level IN ('High', 'Very High', 'Critical')
ORDER BY p.probability DESC;

-- View: revenue at risk summary
CREATE OR REPLACE VIEW revenue_risk_summary AS
SELECT
    p.risk_level,
    COUNT(*) AS customer_count,
    ROUND(SUM(c.monthly_charges), 2) AS monthly_revenue_at_risk,
    ROUND(AVG(p.probability) * 100, 2) AS avg_churn_prob_pct
FROM predictions p
JOIN customers c ON p.customer_id = c.customer_id
GROUP BY p.risk_level
ORDER BY monthly_revenue_at_risk DESC;

-- Procedure: upsert prediction result
CREATE OR REPLACE PROCEDURE upsert_prediction(
    p_customer_id VARCHAR,
    p_label VARCHAR,
    p_probability NUMERIC,
    p_risk_level VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO predictions (customer_id, prediction_label, probability, risk_level)
    VALUES (p_customer_id, p_label, p_probability, p_risk_level);
END;
$$;
