-- SQLite 3.25+. Monetary values are integer USD cents; MRR net of recurring discounts.
DROP TABLE IF EXISTS monthly_snapshot;
CREATE TABLE monthly_snapshot AS
WITH ranked AS (
 SELECT m.month,c.customer_id,c.acquisition_channel,e.plan,e.after_mrr_cents,e.state,
 ROW_NUMBER() OVER(PARTITION BY m.month,c.customer_id ORDER BY e.event_date DESC,e.event_id DESC) rn
 FROM months m JOIN customers c ON c.signup_date<=m.month_end
 JOIN subscription_events e ON e.customer_id=c.customer_id AND e.event_date<=m.month_end
)
SELECT month,customer_id,acquisition_channel,plan,after_mrr_cents mrr_cents,state FROM ranked WHERE rn=1;
CREATE UNIQUE INDEX IF NOT EXISTS snapshot_key ON monthly_snapshot(month,customer_id);
CREATE INDEX IF NOT EXISTS snapshot_customer_month ON monthly_snapshot(customer_id,month);
DROP TABLE IF EXISTS customer_movements;
CREATE TABLE customer_movements AS
WITH grid AS (
 SELECT m.month,c.customer_id,c.acquisition_channel,
 COALESCE(p.mrr_cents,0) opening,COALESCE(s.mrr_cents,0) closing,p.plan opening_plan,s.plan closing_plan,
 EXISTS(SELECT 1 FROM monthly_snapshot h WHERE h.customer_id=c.customer_id AND h.month<m.month AND h.mrr_cents>0) had_paid
 FROM months m JOIN customers c ON c.signup_date<=m.month_end
 LEFT JOIN monthly_snapshot s ON s.month=m.month AND s.customer_id=c.customer_id
 LEFT JOIN monthly_snapshot p ON p.month=date(m.month,'-1 month') AND p.customer_id=c.customer_id
)
SELECT *, CASE WHEN opening=0 AND closing>0 AND had_paid=0 THEN closing ELSE 0 END new_mrr,
 CASE WHEN opening=0 AND closing>0 AND had_paid=1 THEN closing ELSE 0 END reactivation,
 CASE WHEN opening>0 AND closing>opening THEN closing-opening ELSE 0 END expansion,
 CASE WHEN closing>0 AND opening>closing THEN opening-closing ELSE 0 END contraction,
 CASE WHEN opening>0 AND closing=0 THEN opening ELSE 0 END churn,
 (SELECT e.reason FROM subscription_events e WHERE e.customer_id=grid.customer_id AND e.event_date<=date(grid.month,'+1 month','-1 day') AND e.after_mrr_cents=0 ORDER BY e.event_date DESC,e.event_id DESC LIMIT 1) exit_reason
FROM grid;
DROP TABLE IF EXISTS revenue_bridge;
CREATE TABLE revenue_bridge AS
SELECT month,SUM(opening) opening,SUM(new_mrr) new_mrr,SUM(reactivation) reactivation,
 SUM(expansion) expansion,SUM(contraction) contraction,SUM(churn) churn,SUM(closing) closing,
 SUM(CASE WHEN churn>0 AND exit_reason='payment_failure' THEN churn ELSE 0 END) involuntary,
 SUM(opening>0) opening_customers,SUM(churn>0) churned_customers,SUM(closing>0) closing_customers,
 1.0*(SUM(opening)-SUM(contraction)-SUM(churn))/NULLIF(SUM(opening),0) grr,
 1.0*(SUM(opening)+SUM(expansion)-SUM(contraction)-SUM(churn))/NULLIF(SUM(opening),0) nrr,
 SUM(opening)+SUM(new_mrr)+SUM(reactivation)+SUM(expansion)-SUM(contraction)-SUM(churn)-SUM(closing) reconciliation_cents
FROM customer_movements GROUP BY month;
-- Reactivations are excluded from NRR, since they were not in the opening paying cohort.
-- Customer churn = opening payers ending at zero / opening payers.
-- Revenue churn = lost MRR from those customers / opening MRR (contraction shown separately).
-- Endpoint movements net all within-month changes. See event audit for gross activity.
