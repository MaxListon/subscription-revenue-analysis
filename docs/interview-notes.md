# Prepare to explain this project

1. **What is the main result?** Paying customers can rise while MRR falls because new and reactivated revenue plus expansion do not cover existing-customer losses. Explain December with the reconciled bridge.
2. **Why separate MRR, invoices and cash?** MRR is a point-in-time run rate; invoices are prorated charges; cash follows receipt dates. None can substitute for the others.
3. **How does the SQL work?** Read the latest event at each month-end, build a customer-month grain, join prior snapshots, classify mutually exclusive endpoint movements, then aggregate and reconcile.
4. **Why do GRR and NRR differ?** NRR includes expansion from opening payers; GRR does not. Both exclude new and reactivated revenue.
5. **Why does payment failure not immediately reduce MRR?** The customer remains contracted and active during the grace period. An eventual service cancellation removes MRR.
6. **Why is feature activation not causal evidence?** The generator encodes an association. Customer mix also differs. Propose randomized onboarding and retention by assignment.
7. **How does the retention landmark work?** Activation is known by day 14. Customers must be paying on day 30. Outcomes occur afterward; only sufficiently observed customers are eligible. Reactivation counts as paid at the horizon.
8. **What does scenario uncertainty mean?** Rescue probabilities are assumed, then customer rescues are simulated. Model percentiles are not evidence of real-world efficacy or measured impact.
9. **What are the limitations?** Synthetic behavior, endpoint netting, changing retention eligibility, no acquisition-cost analysis, no intervention costs, and no accounting revenue-recognition model.
10. **What would you improve with real data?** Validate billing events and definitions; analyze matched signup cohorts and acquisition costs; measure retry and onboarding effects in controlled experiments.

Run the project yourself, trace a few customer histories in SQLite, and explain one row of the bridge before using it in interviews.
