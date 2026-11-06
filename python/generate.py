"""Synthetic subscription laboratory. Python 3.10+, standard library only. Seed 7142025."""
import sqlite3,random,calendar,datetime as dt,json,csv,pathlib,zipfile,math
ROOT=pathlib.Path(__file__).resolve().parents[1]; OUT=ROOT/'dist'; DL=OUT/'downloads'; DL.mkdir(exist_ok=True)
rng=random.Random(7142025); start=dt.date(2024,1,1); end=dt.date(2025,12,31)
months=[dt.date(y,m,1) for y in (2024,2025) for m in range(1,13)]
db=ROOT/'subscription_analytics.sqlite'; db.unlink(missing_ok=True); con=sqlite3.connect(db); con.row_factory=sqlite3.Row
con.executescript('''
CREATE TABLE customers(customer_id INTEGER PRIMARY KEY,signup_date TEXT,acquisition_channel TEXT,synthetic INTEGER DEFAULT 1);
CREATE TABLE subscriptions(subscription_id INTEGER PRIMARY KEY,customer_id INTEGER,plan TEXT,start_date TEXT,end_date TEXT,FOREIGN KEY(customer_id) REFERENCES customers);
CREATE TABLE subscription_events(event_id INTEGER PRIMARY KEY,subscription_id INTEGER,customer_id INTEGER,event_date TEXT,event_type TEXT,reason TEXT,plan TEXT,after_mrr_cents INTEGER,state TEXT,discount_pct INTEGER);
CREATE TABLE invoices(invoice_id INTEGER PRIMARY KEY,customer_id INTEGER,invoice_date TEXT,amount_due_cents INTEGER,amount_paid_cents INTEGER,invoice_status TEXT);
CREATE TABLE payments(payment_id INTEGER PRIMARY KEY,invoice_id INTEGER,payment_date TEXT,amount_cents INTEGER);
CREATE TABLE product_usage(usage_id INTEGER PRIMARY KEY,customer_id INTEGER,activity_date TEXT,feature_used TEXT);
CREATE TABLE months(month TEXT PRIMARY KEY,month_end TEXT);
''')
for m in months: con.execute('INSERT INTO months VALUES(?,?)',(str(m),str(m.replace(day=calendar.monthrange(m.year,m.month)[1]))))
channels=['Organic','Referral','Paid search','Paid social']; prices=[4900,14900,39900]; plans=['Starter','Growth','Scale']; eid=sid=iid=pid=uid=0; people=[]; daily={}; pending={}
def event(c,d,typ,reason=''):
 global eid
 eid+=1; con.execute('INSERT INTO subscription_events VALUES(?,?,?,?,?,?,?,?,?,?)',(eid,c['sid'],c['id'],str(d),typ,reason,plans[c['plan']],c['mrr'],c['state'],c['disc']))
def spell(c,d):
 global sid
 sid+=1;c['sid']=sid;con.execute('INSERT INTO subscriptions VALUES(?,?,?,?,NULL)',(sid,c['id'],plans[c['plan']],str(d)))
for mi,m in enumerate(months):
 n=900 if mi==0 else (95 if mi<12 else 60)
 for _ in range(n):
  cid=len(people)+1; signup=m.replace(day=rng.randint(1,28)); channel=rng.choices(channels,[.27,.22,.26,.25])[0]
  activated=rng.random()<{'Organic':.64,'Referral':.75,'Paid search':.42,'Paid social':.26}[channel]
  c=dict(id=cid,signup=signup,channel=channel,activated=activated,plan=rng.choices([0,1,2],[.25,.45,.3] if mi<12 else [.65,.30,.05])[0],disc=20 if rng.random()<.22 else 0,mrr=0,state='pending',sid=None,cancel=None,ever=False)
  people.append(c);con.execute('INSERT INTO customers VALUES(?,?,?,1)',(cid,str(signup),channel))
d=start
while d<=end:
 for c in people:
  if d<c['signup']: continue
  age=(d-c['signup']).days
  if age==0:
   spell(c,d);c['state']='trial';event(c,d,'trial_start')
  if age==7 and c['activated']:
   uid+=1;con.execute('INSERT INTO product_usage VALUES(?,?,?,?)',(uid,c['id'],str(d),'workflow_published'))
  if age==14:
   if rng.random()<(.88 if c['activated'] else .57):
    c['state']='active';c['ever']=True;c['mrr']=round(prices[c['plan']]*(1-c['disc']/100));event(c,d,'conversion')
   else:
    c['state']='expired';event(c,d,'trial_expired');con.execute('UPDATE subscriptions SET end_date=? WHERE subscription_id=?',(str(d),c['sid']))
  if d.day==15 and age>30:
   if c['state']=='active':
    if c['cancel'] and d>=c['cancel']:
     c['mrr']=0;c['state']='cancelled';event(c,d,'cancellation','payment_failure');c['cancel']=None
     con.execute('UPDATE subscriptions SET end_date=? WHERE subscription_id=?',(str(d),c['sid']))
    else:
     base={'Organic':.014,'Referral':.009,'Paid search':.027,'Paid social':.045}[c['channel']]
     hazard=base*(.60 if c['activated'] else 1.5)*(2.4 if d.year==2025 else 1)
     x=rng.random()
     if x<hazard:
      c['mrr']=0;c['state']='cancelled';event(c,d,'cancellation','voluntary');con.execute('UPDATE subscriptions SET end_date=? WHERE subscription_id=?',(str(d),c['sid']))
     elif x<hazard+(.055 if d.year==2025 else .012) and c['plan']>0:
      c['plan']-=1;c['mrr']=round(prices[c['plan']]*(1-c['disc']/100));event(c,d,'downgrade','plan_change')
     elif x<hazard+.075 and c['plan']<2 and c['activated']:
      c['plan']+=1;c['mrr']=round(prices[c['plan']]*(1-c['disc']/100));event(c,d,'upgrade','plan_change')
     elif c['disc'] and age>180 and rng.random()<.2:
      c['disc']=0;c['mrr']=prices[c['plan']];event(c,d,'discount_expiry','discount_expiry')
   elif c['state']=='cancelled' and rng.random()<.025:
    spell(c,d);c['state']='active';c['mrr']=round(prices[c['plan']]*(1-c['disc']/100));event(c,d,'reactivation')
  if c['state']=='active' and d.day in (10,25) and rng.random()<.65:
   uid+=1;con.execute('INSERT INTO product_usage VALUES(?,?,?,?)',(uid,c['id'],str(d),'dashboard_viewed'))
  daily[c['id']]=daily.get(c['id'],0)+c['mrr']/calendar.monthrange(d.year,d.month)[1]
 if d.day==calendar.monthrange(d.year,d.month)[1]:
  for c in people:
   due=round(daily.get(c['id'],0))
   if due<=0:continue
   iid+=1;fail=rng.random()<(.035 if d.year==2024 else .13); paid=0; status='failed' if fail else 'paid';paydate=d+dt.timedelta(days=5)
   if not fail and paydate<=end:paid=due
   if not fail and paydate>end:status='open'
   # No payment outcome is observable before the scheduled first attempt.
   if paydate>end:
    fail=False;status='open'
   if fail:
    if rng.random()<.40 and d+dt.timedelta(days=12)<=end:paid=due;status='recovered';paydate=d+dt.timedelta(days=12)
    elif c['state']=='active':c['cancel']=d+dt.timedelta(days=14)
   con.execute('INSERT INTO invoices VALUES(?,?,?,?,?,?)',(iid,c['id'],str(d),due,paid,status))
   if paid:
    pid+=1;con.execute('INSERT INTO payments VALUES(?,?,?,?)',(pid,iid,str(paydate),paid))
  daily={}
 d+=dt.timedelta(days=1)
con.execute('CREATE INDEX event_customer_date ON subscription_events(customer_id,event_date,event_id)')
con.executescript((ROOT/'sql/analysis.sql').read_text());con.commit()
def rows(q):return [dict(x) for x in con.execute(q)]
bridge=rows('SELECT * FROM revenue_bridge ORDER BY month')
for b in bridge:
 b['new_customers']=con.execute('SELECT COUNT(*) FROM customer_movements WHERE month=? AND new_mrr>0',(b['month'],)).fetchone()[0]
 b['invoiced']=con.execute("SELECT COALESCE(SUM(amount_due_cents),0) FROM invoices WHERE substr(invoice_date,1,7)=?",(b['month'][:7],)).fetchone()[0]
 b['cash']=con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM payments WHERE substr(payment_date,1,7)=?",(b['month'][:7],)).fetchone()[0]
 b['failed_balance']=con.execute("SELECT COALESCE(SUM(amount_due_cents-amount_paid_cents),0) FROM invoices WHERE substr(invoice_date,1,7)=? AND invoice_status='failed'",(b['month'][:7],)).fetchone()[0]
 b['trial_starts']=con.execute("SELECT COUNT(*) FROM customers WHERE substr(signup_date,1,7)=?",(b['month'][:7],)).fetchone()[0]
# Landmark retention: converted and active at day 30; activation measured by day 14, outcome day30+offset.
retention=[];channel_ret=[]
def mrr_at(cid,date):
 x=con.execute('SELECT after_mrr_cents FROM subscription_events WHERE customer_id=? AND event_date<=? ORDER BY event_date DESC,event_id DESC LIMIT 1',(cid,str(date))).fetchone();return x[0] if x else 0
# Derive observed activation from usage records, rather than hidden generator flags.
activated_ids={x[0] for x in con.execute("SELECT DISTINCT u.customer_id FROM product_usage u JOIN customers c USING(customer_id) WHERE feature_used='workflow_published' AND activity_date<=date(c.signup_date,'+14 days')")}
for dim,groups,target in [('activation',[True,False],retention),('channel',channels,channel_ret)]:
 for group in groups:
  for offset in [0,30,60,90,120,180,270,360]:
   elig=[c for c in people if (c['id'] in activated_ids if dim=='activation' else c['channel'])==group and c['signup']+dt.timedelta(days=30+offset)<=end and mrr_at(c['id'],c['signup']+dt.timedelta(days=30))>0]
   k=sum(mrr_at(c['id'],c['signup']+dt.timedelta(days=30+offset))>0 for c in elig);n=len(elig);p=k/n if n else 0
   # Wilson binomial interval, descriptive; customers vary with censoring by horizon.
   z=1.96;den=1+z*z/n if n else 1;center=(p+z*z/(2*n))/den if n else 0;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den if n else 0
   target.append(dict(group=str(group),day=offset,n=n,retained=k,rate=p,low=max(0,center-half),high=min(1,center+half)))
plans_data=rows('''SELECT month,opening_plan plan,COUNT(*) opening_customers,SUM(churn>0) churned,SUM(opening) opening_mrr,SUM(churn) lost_mrr,SUM(contraction) contraction FROM customer_movements WHERE opening>0 GROUP BY month,opening_plan''')
checks={}
checks['all_24_bridges_balance']=all(b['reconciliation_cents']==0 for b in bridge)
checks['snapshot_unique']=con.execute('SELECT COUNT(*) FROM monthly_snapshot').fetchone()[0]==con.execute("SELECT COUNT(*) FROM (SELECT month,customer_id FROM monthly_snapshot GROUP BY 1,2)").fetchone()[0]
checks['invoice_payments_match']=not con.execute('SELECT 1 FROM invoices i LEFT JOIN payments p USING(invoice_id) GROUP BY i.invoice_id HAVING i.amount_paid_cents<>COALESCE(SUM(p.amount_cents),0)').fetchone()
checks['event_subscription_integrity']=not con.execute('SELECT 1 FROM subscription_events e LEFT JOIN subscriptions s USING(subscription_id) WHERE s.subscription_id IS NULL OR s.customer_id<>e.customer_id').fetchone()
checks['all_complications_present']=all(con.execute('SELECT COUNT(*) FROM subscription_events WHERE event_type=?',(t,)).fetchone()[0]>0 for t in ['trial_start','downgrade','upgrade','reactivation','discount_expiry'])
checks['no_future_payment_receipts']=not con.execute('SELECT 1 FROM payments WHERE payment_date>?',(str(end),)).fetchone()
checks['unattempted_year_end_invoices_open']=not con.execute("SELECT 1 FROM invoices WHERE date(invoice_date,'+5 days')>? AND invoice_status<>'open'",(str(end),)).fetchone()
assert all(checks.values()),checks
payload=dict(synthetic=True,seed=7142025,months=bridge,retention=retention,channels=channel_ret,plans=plans_data,checks=checks,counts={t:con.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['customers','subscriptions','subscription_events','invoices','payments','product_usage','monthly_snapshot']})
(OUT/'data.js').write_text('window.DATA='+json.dumps(payload)+';')
(DL/'analytics.json').write_text(json.dumps(payload,indent=2));(DL/'validation.json').write_text(json.dumps(checks,indent=2))
for table in ['customers','subscriptions','subscription_events','invoices','payments','product_usage','monthly_snapshot','customer_movements','revenue_bridge']:
 cur=con.execute('SELECT * FROM '+table)
 with (DL/(table+'.csv')).open('w') as f:
  w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(cur)
con.close()
print(json.dumps({'latest':bridge[-1],'counts':payload['counts'],'checks':checks},indent=2))
