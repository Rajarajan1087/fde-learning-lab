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



#	Deliverable	File Name	Key Requirement
A	Profiling notebook	financeflow_profiling.ipynb	Audit findings + CFO sentence + default rate vs benchmark
        Pyfile  : FinanceFlow\PyNotes\financeflow_profiling.ipynb
        Report: FinanceFlow\Reports\financeflow_Y_profile.html

B	GX notebook	financeflow_gx.ipynb	6 checks with underwriting rule comments + Slack-ready summary
         Pyfile  : FinanceFlow\PyNotes\financeflow_gx.ipynb
        Report: FinanceFlow\Reports\financeflow_gx_report.html       

C+D	Classifier + LangChain notebook	financeflow_model.ipynb	Feature importance chart, 3-part briefs, decision column
         Pyfile  : FinanceFlow\PyNotes\financeflow_model.ipynb

E	n8n workflow	financeflow_n8n_workflow.json	7 nodes; Google Sheets, Slack, Gmail, both branches wired
        Pyfile  : FinanceFlow\Finflow_n8n.json

F	Credit Risk briefing	financeflow_briefing.md or .docx	5 paragraphs, constraints met for each
        Pyfile  : FinanceFlow\financeflow_briefing.md

—	Decisions output	financeflow_decisions_today.csv	All Decline + Review records, 8 columns

        FinanceFlow\Data\Output\financeflow_decisions_today.csv