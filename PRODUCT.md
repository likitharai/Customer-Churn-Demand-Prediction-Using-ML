# RetainIQ product model

RetainIQ is an internal B2B customer-retention workspace. Application users are employees of a subscribing company; the customers being analyzed are records and do not log in.

## Roles

- **Agent**: works the risk queue, views assigned customers, records interactions, creates tasks, runs predictions, and records retention outcomes.
- **Manager**: includes agent capabilities plus portfolio metrics, team visibility, customer assignment, imports, and playbook creation.
- **Admin**: includes manager capabilities plus invitations, roles, model status, audit events, and workspace governance.

## Tenant isolation

Every operational table references an organization. API access resolves the signed-in user's membership and filters records by that organization. Legacy global customer and reporting routes are not registered by the production application.

## Operational lifecycle

1. A manager imports customer data from CSV.
2. The model scores churn probability and stores a versioned prediction.
3. The risk queue ranks probability by annual customer value.
4. An agent reviews the customer profile and selects a playbook.
5. Calls, emails, meetings, sentiment, tasks, and follow-ups are recorded.
6. The agent records whether the customer was retained or churned and the revenue protected.
7. Managers monitor live outcomes; administrators review access and audit events.

## ML governance

Training remains separate from the API. The web application loads promoted artifacts from `ml_pipeline/models`, records the model version with every prediction, and exposes model metadata to managers. New models should be trained, evaluated, registered, and promoted in a controlled release process.

## Commercial roadmap

Before accepting public customers, add verified email delivery, password reset, MFA, rate limiting, subscription billing, metering, CRM integrations, managed PostgreSQL, object storage, centralized monitoring, automated backups, and formal privacy/retention controls.
