-- Decision Intelligence Platform — Database Schema
-- PostgreSQL

CREATE TABLE IF NOT EXISTS customers (
    customer_id       VARCHAR(20) PRIMARY KEY,
    gender            VARCHAR(10),
    senior_citizen    SMALLINT DEFAULT 0,
    partner           VARCHAR(5),
    dependents        VARCHAR(5),
    tenure            INTEGER,
    phone_service     VARCHAR(5),
    multiple_lines    VARCHAR(25),
    internet_service  VARCHAR(20),
    online_security   VARCHAR(25),
    online_backup     VARCHAR(25),
    device_protection VARCHAR(25),
    tech_support      VARCHAR(25),
    streaming_tv      VARCHAR(25),
    streaming_movies  VARCHAR(25),
    contract          VARCHAR(20),
    paperless_billing VARCHAR(5),
    payment_method    VARCHAR(35),
    monthly_charges   NUMERIC(8, 2),
    total_charges     NUMERIC(10, 2),
    churn             VARCHAR(5),
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id                SERIAL PRIMARY KEY,
    customer_id       VARCHAR(20) REFERENCES customers(customer_id),
    prediction_label  VARCHAR(10),
    probability       NUMERIC(5, 4),
    risk_level        VARCHAR(20),
    predicted_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recommendations (
    id              SERIAL PRIMARY KEY,
    customer_id     VARCHAR(20) REFERENCES customers(customer_id),
    action          TEXT,
    priority        VARCHAR(10),
    created_at      TIMESTAMP DEFAULT NOW()
);
