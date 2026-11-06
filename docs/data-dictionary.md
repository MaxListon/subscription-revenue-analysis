# Data dictionary
All monetary fields use integer USD cents. Dates are ISO calendar dates; the observation cutoff is 2025-12-31. CSVs are in `dist/downloads/` and tables are in `subscription_analytics.sqlite`.

| Table | Grain / key | Important fields and meaning |
|---|---|---|
| customers | One customer / customer_id | signup_date, acquisition_channel; synthetic=1 labels fabricated records. |
| subscriptions | One service spell / subscription_id | customer_id, start_date, end_date (exclusive effective cancellation date); plan is starting plan. Reactivation creates a new spell. |
| subscription_events | One state change / event_id | subscription_id, customer_id, event_date, event_type, reason, plan, after_mrr_cents, state, discount_pct. Latest event date then event ID determines state. Event plan is authoritative after changes. |
| invoices | One customer-month charge / invoice_id | customer_id, invoice_date, amount_due_cents, amount_paid_cents, invoice_status at the cutoff. |
| payments | One receipt / payment_id | invoice_id, payment_date, amount_cents. Separate from invoice date. |
| product_usage | One usage event / usage_id | customer_id, activity_date, feature_used; workflow_published is the key activation event. |
| months | One calendar month / month | month is first day, month_end final day. |
| monthly_snapshot | One eligible customer-month / month + customer_id | acquisition_channel, plan, state, mrr_cents at month-end. Includes zero-MRR customers. |
| customer_movements | One customer-month / month + customer_id | opening, closing, new_mrr, reactivation, expansion, contraction, churn, opening_plan, closing_plan, exit_reason. All movement amounts are positive magnitudes. |
| revenue_bridge | One month / month | Aggregated movements, paying-customer counts, grr, nrr, reconciliation_cents. |

Customers join to subscriptions, events, invoices, usage and snapshots by customer_id. Events join to service spells by subscription_id. Payments join to invoices by invoice_id.

Endpoint bridges net within-month changes. A conversion followed by cancellation within the same month may appear in events and invoices without entering the month-end MRR bridge. Churn reason uses the last zero-MRR event through month-end. Opening-plan attribution prevents customers from changing analysis buckets mid-month.

`analytics.json` adds invoiced charges, receipt-date cash, failed invoice balance, signup and new-payer counts, retention eligible counts and Wilson intervals. `scenarios.json` contains the Monte Carlo assumptions and outcomes.
