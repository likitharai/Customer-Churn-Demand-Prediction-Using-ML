-- Seed file: load data from CSV using COPY command
-- Run after schema.sql

-- COPY customers FROM '/path/to/data/processed/cleaned_telco.csv'
-- DELIMITER ',' CSV HEADER;

-- Sample seed row
INSERT INTO customers (customer_id, gender, senior_citizen, tenure, monthly_charges, total_charges, contract, churn)
VALUES ('SAMPLE-001', 'Male', 0, 12, 70.00, 840.00, 'Month-to-month', 'No')
ON CONFLICT DO NOTHING;
