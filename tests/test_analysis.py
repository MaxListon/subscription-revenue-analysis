"""Regression tests against hand-calculated event histories and generated outputs."""
import unittest,sqlite3,pathlib,json,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
class RevenueContract(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
  self.db.executescript('''CREATE TABLE customers(customer_id INTEGER,signup_date TEXT,acquisition_channel TEXT);
CREATE TABLE months(month TEXT,month_end TEXT);
CREATE TABLE subscription_events(event_id INTEGER,customer_id INTEGER,event_date TEXT,plan TEXT,after_mrr_cents INTEGER,state TEXT,reason TEXT);
INSERT INTO months VALUES('2025-01-01','2025-01-31'),('2025-02-01','2025-02-28'),('2025-03-01','2025-03-31');''')
 def tearDown(self):self.db.close()
 def customer(self,cid,events):
  self.db.execute('INSERT INTO customers VALUES(?,?,?)',(cid,'2025-01-01','Organic'))
  for date,mrr,reason in events:
   eid=self.db.execute('SELECT COUNT(*)+1 FROM subscription_events').fetchone()[0]
   self.db.execute('INSERT INTO subscription_events VALUES(?,?,?,?,?,?,?)',(eid,cid,date,'Growth',mrr,'active' if mrr else 'cancelled',reason))
 def run_sql(self):self.db.executescript((R/'sql/analysis.sql').read_text())
 def movement(self,month):return self.db.execute('SELECT * FROM customer_movements WHERE month=?',(month,)).fetchone()
 def test_trial_to_paid_is_new_not_expansion(self):
  self.customer(1,[('2025-01-01',0,'trial'),('2025-02-14',10000,'')]);self.run_sql();m=self.movement('2025-02-01');self.assertEqual((m['new_mrr'],m['expansion']),(10000,0))
 def test_churn_then_return_is_reactivation(self):
  self.customer(1,[('2025-01-10',10000,''),('2025-02-10',0,'voluntary'),('2025-03-10',10000,'')]);self.run_sql();m=self.movement('2025-03-01');self.assertEqual((m['reactivation'],m['new_mrr']),(10000,0))
 def test_downgrade_is_contraction_not_churn(self):
  self.customer(1,[('2025-01-10',10000,''),('2025-02-15',6000,'')]);self.run_sql();m=self.movement('2025-02-01');self.assertEqual((m['contraction'],m['churn']),(4000,0))
 def test_nrr_excludes_new_customers(self):
  self.customer(1,[('2025-01-10',10000,''),('2025-02-15',12000,'')]);self.customer(2,[('2025-02-10',90000,'')]);self.run_sql();m=self.db.execute("SELECT * FROM revenue_bridge WHERE month='2025-02-01'").fetchone();self.assertAlmostEqual(m['grr'],1);self.assertAlmostEqual(m['nrr'],1.2)
 def test_same_day_latest_event_wins(self):
  self.customer(1,[('2025-01-31',10000,''),('2025-01-31',15000,'')]);self.run_sql();self.assertEqual(self.movement('2025-01-01')['closing'],15000)
 def test_in_month_round_trip_is_netted(self):
  self.customer(1,[('2025-01-01',0,'trial'),('2025-02-05',10000,''),('2025-02-20',0,'voluntary')]);self.run_sql();m=self.movement('2025-02-01');self.assertEqual((m['new_mrr'],m['churn'],m['closing']),(0,0,0))
 def test_payment_cancellation_reason(self):
  self.customer(1,[('2025-01-10',10000,''),('2025-02-15',0,'payment_failure')]);self.run_sql();m=self.db.execute("SELECT * FROM revenue_bridge WHERE month='2025-02-01'").fetchone();self.assertEqual((m['involuntary'],m['reconciliation_cents']),(10000,0))
 def test_empty_opening_retention_is_undefined(self):
  self.customer(1,[('2025-01-10',10000,'')]);self.run_sql();m=self.db.execute('SELECT * FROM revenue_bridge ORDER BY month LIMIT 1').fetchone();self.assertIsNone(m['grr']);self.assertIsNone(m['nrr'])
 def test_sql_rebuild_is_idempotent(self):
  self.customer(1,[('2025-01-10',10000,''),('2025-02-15',5000,'')]);self.run_sql();before=[tuple(r) for r in self.db.execute('SELECT * FROM revenue_bridge')];self.run_sql();self.assertEqual(before,[tuple(r) for r in self.db.execute('SELECT * FROM revenue_bridge')])
class GeneratedArtifacts(unittest.TestCase):
 def test_validation_and_observation_cutoff(self):
  checks=json.loads((R/'dist/downloads/validation.json').read_text());self.assertTrue(all(checks.values()));self.assertTrue(checks['unattempted_year_end_invoices_open'])
 def test_analysis_preserves_readme(self):
  before=(R/'README.md').read_bytes();subprocess.run([sys.executable,str(R/'python/analyze.py')],check=True,stdout=subprocess.DEVNULL);self.assertEqual(before,(R/'README.md').read_bytes())
 def test_payment_ledger_and_bridge_balance(self):
  with sqlite3.connect(R/'subscription_analytics.sqlite') as db:
   self.assertEqual(db.execute('SELECT COUNT(*) FROM revenue_bridge WHERE reconciliation_cents<>0').fetchone()[0],0)
   self.assertEqual(db.execute('SELECT SUM(amount_paid_cents) FROM invoices').fetchone()[0],db.execute('SELECT SUM(amount_cents) FROM payments').fetchone()[0])
if __name__=='__main__':unittest.main()
