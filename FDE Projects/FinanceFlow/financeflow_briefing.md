# FinanceFlow Capital — AI Credit Decisioning: Briefing for Head of Credit Risk

**Prepared by:** Rajarajan Venkatesan, Senior Forward Deployed AI Engineer  
**Date:** 14 June 2026  
**Status:** Pilot Complete — Awaiting Production Sign-off

---

## 1. The Data Situation

We reviewed 400 historical loan records exported from the core banking system 
and found that 70 records were unusable — 30 were missing a credit score, 
25 had no recorded outcome, and 15 showed negative revenue figures that 
suggest data entry errors. This means the system was trained on 330 verified 
records, which is sufficient for a pilot but will need to grow over time as 
more clean history accumulates. The data team should treat these 70 records 
as a priority cleanup item. Until the source data improves, the system will 
flag and block any morning batch that contains similar problems.

---

## 2. The Model

The system reviews each loan application and produces a score between 0 and 1 
representing how likely the business is to be unable to repay. Based on that 
score, every application receives one of three flags — Approve, Review, or 
Decline. The system does not make final decisions; it organises the analyst's 
workload so that time is spent on the applications that genuinely need human 
judgement. The three factors the system weighs most heavily are how long the 
business has been operating, the applicant's credit history, and how much of 
their current income is already committed to existing debt obligations.

---

## 3. The Automation

Every morning the following steps happen without manual intervention:

1. At 8:00 AM the system retrieves the overnight batch of new loan applications 
   from the core banking system.
2. The batch is checked against a data contract — any missing credit scores, 
   missing outcome records, or negative revenue figures cause the batch to be 
   blocked and the data operations team is alerted on Slack immediately.
3. If the batch passes the quality check, every application is scored and 
   flagged as Approve, Review, or Decline.
4. Decline and Review applications are written to the analyst work queue in 
   Google Sheets and underwriter briefs are emailed to the credit analyst 
   before the morning standup.
5. A summary is posted to the #credit-team Slack channel showing the count of 
   each decision and the total loan value requiring analyst attention that day.

---

## 4. Limitations and Risks

**The system misses roughly 6 in 10 actual defaults in the Approve pile.**  
Applications flagged as Approve have passed the scoring threshold, but the 
system is not infallible. Analysts should treat the Approve pile as lower 
priority — not zero risk. Periodic spot checks on approved loans are strongly 
recommended.

**The Decline flag is a strong recommendation, not a final verdict.**  
Every Decline the system raises has been accurate in testing, but the system 
was tested on the same population it was trained on. Analysts must perform a 
brief manual confirmation before rejecting any application — particularly for 
sectors or geographies underrepresented in the training data.

---

## 5. The Ask

The Head of Credit Risk must confirm the three decision thresholds — Approve 
below 40%, Review between 40–64%, Decline at 65% and above — as the official 
underwriting policy by June 30, 2026, so the system can be moved from pilot 
to production without liability ambiguity.