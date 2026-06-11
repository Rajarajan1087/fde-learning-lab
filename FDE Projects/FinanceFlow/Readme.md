==Problem Statement_RAW: ==

FinanceFlow Capital is a digital lender offering working capital loans to small and medium
businesses across the US. Their current underwriting process takes 3–5 business days and
relies on a credit analyst manually reviewing each application. The Head of Credit Risk
wants an AI-assisted triage system: automatically flag applications likely to default so
analysts can focus their time on borderline and high-value cases.
You are the lead FDE. On Day 1, their data team exports 400 historical loan records from
their core banking system. Your task is to audit the data, build the risk classifier, wire
the automated decisioning workflow, and hand off a system the credit team can run daily
without your involvement.


==Y Profiling Analysis :==


## Data Contract Status

- ✅ **Loan scoring ranges and business categories are clean** — all 400 records have valid
  credit score ranges, acceptable debt levels, and recognised business sectors.
  These fields are ready for the model.

- ⚠️ **30 applications are missing a credit score** — without this, the system cannot
  generate a risk score for those borrowers. These records will be excluded from
  today's decisioning run until the data is resubmitted.

- ⚠️ **40 records have data issues blocking model training** — 25 applications have no
  outcome history (we cannot tell if they defaulted), and 15 show negative revenue
  figures which are likely data entry errors. These have been quarantined and will
  not influence the model.
