# Revenue is falling despite customer acquisition
**Executive case study · Synthetic data · January 2024–December 2025 · USD · Seed 7142025**

## Decision in one minute
December ends at **$95,774 MRR**, down $1,810 from its opening level. The company adds **52 new month-end paying customers** and has 60 signups, yet contraction and churn exceed new, reactivated and expansion MRR. Paying customers increase from 650 to 660, illustrating why customer counts alone hide loss of value.

MRR falls 57.3% from December 2024 ($224,342). The simulation deliberately introduces a 2025 shift toward cheaper new plans, higher cancellation hazards, downgrades, and payment failures. This is an explanation of a constructed dataset, not evidence about an actual company.

## What caused the December decline?
| Movement | MRR |
|---|---:|
| Opening | $97,584 |
| New | +$4,870 |
| Reactivation | +$5,458 |
| Existing-customer expansion | +$1,859 |
| Contraction | −$2,960 |
| Voluntary cancellation | −$3,555 |
| Payment-failure cancellation | −$7,483 |
| Closing | $95,774 |
| Reconciliation difference | **$0.00** |

Payment-failure cancellations account for 53.5% of total churn plus contraction MRR loss in December. Failed invoices do not themselves reduce MRR; they reduce cash and trigger cancellation after a grace period if unrecovered. December's failed invoice balance is $0, a separate stock measured at the dataset cutoff. It must not be added to churn as another MRR loss.

Expansion contributes $1,859, or 15.3% of December gross positive MRR movements. It includes upgrades and discount expirations, net of other within-month changes for each opening payer. It is a movement, not a separable share of total closing revenue. GRR is **85.7%** and NRR is **87.6%**.

## Acquisition and activation
90-day point-in-time paid retention after the day-30 landmark:

| Channel | Eligible customers | Retention | 95% Wilson interval |
|---|---:|---:|---:|
| Organic | 487 | 88.7% | 85.6%–91.2% |
| Referral | 399 | 85.2% | 81.4%–88.4% |
| Paid search | 478 | 79.7% | 75.9%–83.1% |
| Paid social | 401 | 74.6% | 70.1%–78.6% |

- Activated: 86.0% retained, n=1088.
- Not activated: 76.2% retained, n=677.

Activation means publishing a workflow within 14 days. The common day-30 landmark avoids classifying customers using future activation behavior. Only day-30 payers with sufficient follow-up enter each horizon. Retention includes reactivation at the horizon, so these are not Kaplan–Meier survival curves. Rates at different horizons have different eligible cohorts. Plan, channel and signup mix confound comparisons; activation's association was intentionally encoded by the generator. Wilson intervals describe binomial sampling variation, not synthetic model uncertainty.

## Plan churn: count versus value
| Opening plan | Customer churn | Revenue churn | Contraction MRR |
|---|---:|---:|---:|
| Growth | 13.5% | 13.4% | $1,460 |
| Scale | 10.0% | 10.0% | $1,500 |
| Starter | 10.4% | 10.2% | $0 |

Rates use opening-plan attribution, so downgrading customers remain assigned to their opening plan for this comparison. Customer churn counts opening payers ending at zero / opening payers. Revenue churn is their lost opening MRR / opening MRR. Contraction is excluded from churn; gross revenue loss includes both.

## Prioritized actions and scenario uncertainty
1. **Recover failed payments:** Test reminder timing, payment-method updates and retries with a randomized holdout. Evaluate incremental cash and involuntary MRR saved, net of retry costs; track complaints. This directly addresses December's largest loss category.
2. **Prevent high-value cancellations and downgrades:** Interview Growth/Scale exits; test targeted value or packaging changes. Measure opening-cohort NRR and gross margin, guarding against discount-driven apparent retention.
3. **Test activation improvements:** Randomize onboarding to workflow publication, measuring paid retention at 90 days by assignment. Treat channel rankings as diagnostic signals until acquisition costs and comparable cohorts are available.

A one-month scenario rescuing 30% of voluntary cancellation MRR and 40% of payment-failure cancellation MRR preserves **$4,060 MRR**, implying **$99,833** closing MRR. The dashboard offers adjustable assumptions and deterministic sensitivity bounds.

The Python model additionally draws voluntary rescue probability uniformly from 15–45% and payment rescue probability from 25–55%, then independently rescues individual lost customers at their opening MRR. Across 10,000 trials (seed 7142026), the 5th–95th percentile increment is **$2,355–$5,814**. These are illustrative model outcomes, not empirical confidence bounds. Assumptions: rescued customers keep their opening plans through month-end; no interaction, extra expansion, new acquisition, costs, cash uplift or compounding. The simulation and dashboard use the same central efficacy, but their ranges differ: customer-level randomness versus deterministic efficacy bounds.

## Metric and accounting contract
- **MRR:** month-end active contracted monthly price, net of recurring discounts; trials and cancelled service contribute zero. Past-due service stays in MRR until cancellation. USD cents are integers.
- **Invoiced charges:** sum of daily active net MRR / days in that calendar month, rounded once per customer/month and billed in arrears. Mid-month changes therefore prorate exactly under this model. These are service charges, not GAAP recognized revenue.
- **Collected cash:** payments with receipt date in the month. Receipts are five days after invoice, or twelve days for recovered failures. December's open invoices are outside the cash window, not failed payments.
- **New MRR:** first positive month-end snapshot; reactivation requires an earlier positive month-end and zero opening MRR.
- **Expansion/contraction:** positive/negative net change among customers paying at both month endpoints. Reactivations and new MRR are excluded from NRR because they are outside the opening paying cohort.
- **GRR:** (opening − contraction − churn) / opening. **NRR:** (opening + expansion − contraction − churn) / opening. Undefined if opening is zero.
- **Bridge:** opening + new + reactivation + expansion − contraction − churn = closing. All 24 bridges reconcile to zero cents. Endpoint netting means a conversion and cancellation in the same month need not enter MRR movements; events and invoices preserve that activity.
- Subscription rows represent service spells. Event plan is authoritative after mid-spell changes. Dates are effective at start of day; month-end snapshots include all events on the final day. State is determined by latest date then event ID. No annual billing, tax, refunds or FX.

## Reproducibility and checks
Run `python3 python/generate.py`, then `python3 python/analyze.py` from the project directory. Standard library only; no external services or paid APIs. Regeneration overwrites the synthetic database and exports. The SQL is runnable against the raw generated SQLite tables and rebuilds the modeled tables.

Checks cover every revenue bridge, unique customer-month grain, invoice-to-payment equality, event/subscription ownership, and presence of every requested complication. The project contains 2,665 customers, 20,728 invoices and 45,090 customer-month snapshots. See `validation.json` for results and CSV/SQLite files for audit.

**Limitation:** Synthetic data demonstrates the methods; it does not establish real customer behavior. Statistical intervals do not validate the generator's assumptions or real-world intervention effects.
