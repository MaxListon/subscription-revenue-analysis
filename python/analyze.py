"""Produce executive report, standalone SVG charts and assumption-driven Monte Carlo scenarios."""
import pathlib,json,random,statistics,csv,sqlite3,shutil
R=pathlib.Path(__file__).resolve().parents[1];D=R/'dist';O=D/'downloads';a=json.loads((O/'analytics.json').read_text());bs=a['months'];b=bs[-1];prev=bs[11]
fmt=lambda x:f'${x/100:,.0f}'
pct=lambda x:f'{x*100:.1f}%'
con=sqlite3.connect(R/'subscription_analytics.sqlite')
# Independent customer-level Bernoulli rescue; efficacy drawn once per scenario trial.
losses=con.execute("SELECT churn,exit_reason FROM customer_movements WHERE month=? AND churn>0", (b['month'],)).fetchall();rng=random.Random(7142026);sim=[]
for _ in range(10000):
 v=rng.uniform(.15,.45);p=rng.uniform(.25,.55)
 sim.append(sum(loss for loss,reason in losses if rng.random()<(p if reason=='payment_failure' else v)))
sim.sort();scenario={'baseline_mrr_cents':b['closing'],'expected_increment_cents':.3*(b['churn']-b['involuntary'])+.4*b['involuntary'],'simulated_increment_mean_cents':statistics.mean(sim),'p05_increment_cents':sim[499],'p95_increment_cents':sim[9499],'draws':10000,'seed':7142026,'assumptions':{'voluntary_rescue_probability':'Uniform(0.15,0.45)','payment_failure_rescue_probability':'Uniform(0.25,0.55)','rescue_unit':'customer Bernoulli, opening MRR preserved','horizon':'one month, no compounding','costs':'excluded','interpretation':'model-based predictive sensitivity; not a real-world confidence interval'}}
(O/'scenarios.json').write_text(json.dumps(scenario,indent=2))
# Dependency-free, standalone vector figures generated in Python.
colors=['#14796c','#b75042','#54718c'];svghead='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="420" viewBox="0 0 1000 420"><rect width="1000" height="420" fill="#f4f6f3"/>'
def chart(title,series,labels,maximum,path,percent=False):
 xp=lambda i:80+(float(labels[i][:-1])/float(labels[-1][:-1]) if percent else i/(len(labels)-1))*870
 s=svghead+f'<text x="65" y="36" font-family="sans-serif" font-size="22" fill="#182a30">{title}</text>'
 for i in range(5):
  y=70+i*65;val=maximum*(1-i/4);lab=f'{val:.0%}' if percent else fmt(val)
  s+=f'<path d="M80 {y}H950" stroke="#dce3df"/><text x="72" y="{y+4}" text-anchor="end" font-family="sans-serif" font-size="12">{lab}</text>'
 for si,(name,values) in enumerate(series):
  pts=' '.join(f'{xp(i):.2f},{70+260*(1-v/maximum):.2f}' for i,v in enumerate(values))
  s+=f'<polyline points="{pts}" fill="none" stroke="{colors[si]}" stroke-width="3"/><text x="{80+si*280}" y="395" font-size="13" font-family="sans-serif" fill="{colors[si]}">{name}</text>'
 for i,lab in enumerate(labels):
  if len(labels)<10 or i%6==0 or i==len(labels)-1:s+=f'<text x="{xp(i):.2f}" y="355" text-anchor="middle" font-size="12" font-family="sans-serif">{lab}</text>'
 path.write_text(s+'</svg>')
chart('SYNTHETIC · Recurring revenue, invoiced charges and cash',[(k,[x[v] for x in bs]) for k,v in [('Net MRR','closing'),('Invoiced','invoiced'),('Cash received','cash')]], [x['month'][:7] for x in bs],max(x['closing'] for x in bs)*1.15,O/'revenue-trend.svg')
chart('SYNTHETIC · Point-in-time paid retention after day-30 landmark',[(label,[x['rate'] for x in a['retention'] if x['group']==g]) for label,g in [('Activated by day 14','True'),('Not activated','False')]], [str(x['day'])+'d' for x in a['retention'] if x['group']=='True'],1,O/'retention.svg',True)
vals=[b['opening'],b['new_mrr'],b['reactivation'],b['expansion'],-b['contraction'],-b['churn'],b['closing']];labs=['Opening','New','Reactivation','Expansion','Contraction','Churn','Closing'];mx=(b['opening']+sum(vals[1:4]))*1.15;s=svghead+'<text x="40" y="36" font-family="sans-serif" font-size="22">SYNTHETIC · December 2025 MRR bridge</text>';run=0
for i,(v,l) in enumerate(zip(vals,labs)):
 f=0 if i in (0,6) else run;t=v if i in (0,6) else run+v;y=330-max(f,t)/mx*240;h=abs(t-f)/mx*240;x=35+i*138;s+=f'<rect x="{x}" y="{y}" width="100" height="{max(1,h)}" fill="{colors[1] if v<0 else colors[0]}"/><text x="{x+50}" y="{y-10}" text-anchor="middle" font-family="sans-serif" font-size="13">{fmt(v)}</text><text x="{x+50}" y="355" text-anchor="middle" font-family="sans-serif" font-size="12">{l}</text>';run=t
(O/'revenue-movement.svg').write_text(s+'</svg>')
channels=sorted([x for x in a['channels'] if x['day']==90],key=lambda x:-x['rate']);act=[x for x in a['retention'] if x['day']==90];plans=[x for x in a['plans'] if x['month']==b['month']]
report=f'''# Revenue is falling despite customer acquisition
**Executive case study · Synthetic data · January 2024–December 2025 · USD · Seed 7142025**

## Decision in one minute
December ends at **{fmt(b['closing'])} MRR**, down {fmt(b['opening']-b['closing'])} from its opening level. The company adds **{b['new_customers']} new month-end paying customers** and has {b['trial_starts']} signups, yet contraction and churn exceed new, reactivated and expansion MRR. Paying customers increase from {b['opening_customers']} to {b['closing_customers']}, illustrating why customer counts alone hide loss of value.

MRR falls {pct(1-b['closing']/prev['closing'])} from December 2024 ({fmt(prev['closing'])}). The simulation deliberately introduces a 2025 shift toward cheaper new plans, higher cancellation hazards, downgrades, and payment failures. This is an explanation of a constructed dataset, not evidence about an actual company.

## What caused the December decline?
| Movement | MRR |
|---|---:|
| Opening | {fmt(b['opening'])} |
| New | +{fmt(b['new_mrr'])} |
| Reactivation | +{fmt(b['reactivation'])} |
| Existing-customer expansion | +{fmt(b['expansion'])} |
| Contraction | −{fmt(b['contraction'])} |
| Voluntary cancellation | −{fmt(b['churn']-b['involuntary'])} |
| Payment-failure cancellation | −{fmt(b['involuntary'])} |
| Closing | {fmt(b['closing'])} |
| Reconciliation difference | **$0.00** |

Payment-failure cancellations account for {pct(b['involuntary']/(b['churn']+b['contraction']))} of total churn plus contraction MRR loss in December. Failed invoices do not themselves reduce MRR; they reduce cash and trigger cancellation after a grace period if unrecovered. December's failed invoice balance is {fmt(b['failed_balance'])}, a separate stock measured at the dataset cutoff. It must not be added to churn as another MRR loss.

Expansion contributes {fmt(b['expansion'])}, or {pct(b['expansion']/(b['new_mrr']+b['reactivation']+b['expansion']))} of December gross positive MRR movements. It includes upgrades and discount expirations, net of other within-month changes for each opening payer. It is a movement, not a separable share of total closing revenue. GRR is **{pct(b['grr'])}** and NRR is **{pct(b['nrr'])}**.

## Acquisition and activation
90-day point-in-time paid retention after the day-30 landmark:

| Channel | Eligible customers | Retention | 95% Wilson interval |
|---|---:|---:|---:|
'''+''.join(f"| {x['group']} | {x['n']} | {pct(x['rate'])} | {pct(x['low'])}–{pct(x['high'])} |\n" for x in channels)+ '\n'+''.join(f"- {'Activated' if x['group']=='True' else 'Not activated'}: {pct(x['rate'])} retained, n={x['n']}.\n" for x in act)+f'''
Activation means publishing a workflow within 14 days. The common day-30 landmark avoids classifying customers using future activation behavior. Only day-30 payers with sufficient follow-up enter each horizon. Retention includes reactivation at the horizon, so these are not Kaplan–Meier survival curves. Rates at different horizons have different eligible cohorts. Plan, channel and signup mix confound comparisons; activation's association was intentionally encoded by the generator. Wilson intervals describe binomial sampling variation, not synthetic model uncertainty.

## Plan churn: count versus value
| Opening plan | Customer churn | Revenue churn | Contraction MRR |
|---|---:|---:|---:|
'''+''.join(f"| {p['plan']} | {pct(p['churned']/p['opening_customers'])} | {pct(p['lost_mrr']/p['opening_mrr'])} | {fmt(p['contraction'])} |\n" for p in plans)+f'''
Rates use opening-plan attribution, so downgrading customers remain assigned to their opening plan for this comparison. Customer churn counts opening payers ending at zero / opening payers. Revenue churn is their lost opening MRR / opening MRR. Contraction is excluded from churn; gross revenue loss includes both.

## Prioritized actions and scenario uncertainty
1. **Recover failed payments:** Test reminder timing, payment-method updates and retries with a randomized holdout. Evaluate incremental cash and involuntary MRR saved, net of retry costs; track complaints. This directly addresses December's largest loss category.
2. **Prevent high-value cancellations and downgrades:** Interview Growth/Scale exits; test targeted value or packaging changes. Measure opening-cohort NRR and gross margin, guarding against discount-driven apparent retention.
3. **Test activation improvements:** Randomize onboarding to workflow publication, measuring paid retention at 90 days by assignment. Treat channel rankings as diagnostic signals until acquisition costs and comparable cohorts are available.

A one-month scenario rescuing 30% of voluntary cancellation MRR and 40% of payment-failure cancellation MRR preserves **{fmt(scenario['expected_increment_cents'])} MRR**, implying **{fmt(b['closing']+scenario['expected_increment_cents'])}** closing MRR. The dashboard offers adjustable assumptions and deterministic sensitivity bounds.

The Python model additionally draws voluntary rescue probability uniformly from 15–45% and payment rescue probability from 25–55%, then independently rescues individual lost customers at their opening MRR. Across 10,000 trials (seed 7142026), the 5th–95th percentile increment is **{fmt(scenario['p05_increment_cents'])}–{fmt(scenario['p95_increment_cents'])}**. These are illustrative model outcomes, not empirical confidence bounds. Assumptions: rescued customers keep their opening plans through month-end; no interaction, extra expansion, new acquisition, costs, cash uplift or compounding. The simulation and dashboard use the same central efficacy, but their ranges differ: customer-level randomness versus deterministic efficacy bounds.

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

Checks cover every revenue bridge, unique customer-month grain, invoice-to-payment equality, event/subscription ownership, and presence of every requested complication. The project contains {a['counts']['customers']:,} customers, {a['counts']['invoices']:,} invoices and {a['counts']['monthly_snapshot']:,} customer-month snapshots. See `validation.json` for results and CSV/SQLite files for audit.

**Limitation:** Synthetic data demonstrates the methods; it does not establish real customer behavior. Statistical intervals do not validate the generator's assumptions or real-world intervention effects.
'''
(O/'executive-report.md').write_text(report)
shutil.copy(R/'sql/analysis.sql',O/'analysis.sql')
print(json.dumps(scenario,indent=2))

brief=f"""# New customers. Less revenue.
**Executive brief · Synthetic case study · December 2025 · USD**

Paying customers rise from **{b['opening_customers']} to {b['closing_customers']}**, including **{b['new_customers']} new month-end payers**, while MRR falls **{fmt(b['opening']-b['closing'])} ({pct(1-b['closing']/b['opening'])})** to **{fmt(b['closing'])}**.

## Why revenue fell
Opening {fmt(b['opening'])} + new {fmt(b['new_mrr'])} + reactivation {fmt(b['reactivation'])} + expansion {fmt(b['expansion'])} − contraction {fmt(b['contraction'])} − voluntary cancellation {fmt(b['churn']-b['involuntary'])} − payment-related cancellation {fmt(b['involuntary'])} = closing {fmt(b['closing'])}. Calculation in cents balances exactly; displayed dollars are rounded.

Payment-related cancellation contributes **{pct(b['involuntary']/(b['churn']+b['contraction']))}** of churn plus contraction MRR loss. GRR is **{pct(b['grr'])}** and NRR is **{pct(b['nrr'])}**. Existing-customer expansion contributes {fmt(b['expansion'])}, or {pct(b['expansion']/(b['new_mrr']+b['reactivation']+b['expansion']))} of positive MRR movements.

## Retention findings
The highest observed channel retention at 90 days after the day-30 landmark is **{channels[0]['group']} ({pct(channels[0]['rate'])}, n={channels[0]['n']})**. Activated customers retain at {pct(act[0]['rate'])} versus {pct(act[1]['rate'])} for others. These are descriptive comparisons with confounding and generator-encoded relationships, not causal evidence. **{max(plans,key=lambda p:p['churned']/p['opening_customers'])['plan']}** has the highest customer churn rate; **{max(plans,key=lambda p:p['lost_mrr']/p['opening_mrr'])['plan']}** has the highest revenue churn rate in December.

## Prioritize interventions
1. **Recover failed payments:** randomize reminders and retries; measure incremental cash and involuntary MRR saved net of costs.
2. **Retain high-value customers:** interview Growth/Scale exits and test value or packaging changes, with NRR and margin guardrails.
3. **Test activation improvements:** randomize workflow onboarding and measure 90-day paid retention by assignment.

Preserving 30% of voluntary and 40% of involuntary cancellation MRR adds **{fmt(scenario['expected_increment_cents'])}**, implying **{fmt(b['closing']+scenario['expected_increment_cents'])}** closing MRR. The 10,000-draw simulation yields a 5th–95th percentile uplift of **{fmt(scenario['p05_increment_cents'])}–{fmt(scenario['p95_increment_cents'])}**. These are assumed one-month effects, not forecasts; costs, cash uplift and compounding are excluded.

## Three separate money measures
- **MRR: {fmt(b['closing'])}.** Month-end contracted run rate net of recurring discounts.
- **Invoiced charges: {fmt(b['invoiced'])}.** Prorated service charges billed in arrears, not GAAP recognized revenue.
- **Cash received: {fmt(b['cash'])}.** Receipts dated in December, including earlier invoices. Attempts dated after the observation cutoff remain open rather than failed.

All 24 monthly bridges reconcile to zero cents. **All data is synthetic; this demonstrates methods and does not establish actual customer behavior.**
"""
(O/'executive-brief.md').write_text(brief)
con.close()
