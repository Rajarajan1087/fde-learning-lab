# FinSight — Loan Default Prediction & Risk Intelligence Automation

![Python](https://img.shields.io/badge/Python-3.10-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-orange)
![LangChain](https://img.shields.io/badge/LangChain-0.2+-green)
![n8n](https://img.shields.io/badge/n8n-cloud-purple)
![Mistral](https://img.shields.io/badge/LLM-Mistral--Small-red)
![Great Expectations](https://img.shields.io/badge/GX-1.18.1-lightgrey)

> End-to-end loan default risk pipeline: data audit → ML scoring → LLM-generated branch manager alerts → live automation workflow. Built as part of the IIT Roorkee Forward Deployed AI Engineering program.

--

## Problem Statement

FinSight Capital's credit team manually reviews hundreds of loan applications with no automated data quality checks, no consistent risk scoring, and no real-time alerts to branch managers. High-risk applications slip through because the process depends on individual analyst judgment rather than a repeatable, auditable system.

This project builds that system — from raw CSV to a live webhook-triggered workflow that scores every application, generates a branch manager alert using an LLM, and logs everything to Google Sheets in under 10 seconds.

---

## Architecture

```
Raw CSV (2,000 applications)
       │
       ▼
┌─────────────────┐
│  Part A         │  ydata-profiling audit + CFO memo
│  Data Audit     │  5 missing income, 6 missing credit scores flagged
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Part B         │  Great Expectations — 6 regulatory checks
│  GX Validation  │  2 FAILED: credit_score null, annual_income null
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Part C1        │  Random Forest (n_estimators=150) + SMOTE
│  ML Classifier  │  Recall: 0.901 | ROC-AUC: 0.947 | Threshold: 0.3
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Part C2        │  LangChain + Mistral Small
│  Alert Engine   │  110 high-risk alerts — 3-sentence branch manager notes
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Part D — Live n8n Workflow                 │
│                                             │
│  Postman/System → Webhook                   │
│       │                                     │
│  Flask API (ML Score + Mistral Alert)       │
│       │                                     │
│  High Risk? ──TRUE──→ Slack Alert           │
│                   └──→ Gmail to Branch Mgr  │
│                   └──→ Google Sheets Log    │
│       │                                     │
│  FALSE ──────────→ Google Sheets Log        │
└─────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data Profiling | ydata-profiling 4.x |
| Data Validation | Great Expectations 1.18.1 |
| ML Model | scikit-learn Random Forest + imbalanced-learn SMOTE |
| LLM Orchestration | LangChain 0.2+ |
| Alert Generation | Mistral Small (mistral-small-latest) |
| API Layer | Flask + ngrok |
| Automation | n8n Cloud |
| Notifications | Slack, Gmail |
| Logging | Google Sheets |
| Environment | Google Colab |

---

## LLM Journey — Why Mistral

Three LLMs were attempted before settling on Mistral:

**Groq (LLaMA-3.3-70b)** — First choice due to free tier availability. Hit the 100,000 token/day limit at alert 22 of 110. Retry logic with 3-minute waits made the batch run impractical (estimated 3.5 hours).

**Gemini 2.0 Flash** — Switched for higher limits. Hit the 5 requests/minute free tier ceiling immediately. With 13-second sleep between requests, estimated completion time was 24 minutes with Colab disconnect risk.

**Mistral Small** — Final choice. 1 request/second free tier, no daily token cap on small models. All 110 alerts completed in under 4 minutes. Alert quality matched Gemini on 3-sentence prose format evaluation.

**Key learning:** For batch LLM jobs on free tiers, rate limits matter more than model quality. Mistral's architecture is the better fit for this use case.

---

## Model Performance

| Metric | Value |
|---|---|
| Accuracy | 0.830 |
| Precision | 0.637 |
| Recall | **0.901** |
| F1 Score | 0.746 |
| ROC-AUC | 0.947 |
| Threshold | 0.3 |

**Why threshold 0.3, not 0.5:**
At threshold 0.5, Recall dropped to 0.845 — 1 in 6 defaulters passed through undetected. In credit risk, a missed defaulter costs the bank principal loss. A false alarm costs only additional review time. Threshold lowered to 0.3 to prioritise catching defaulters.

**Class imbalance handling:**
Dataset had 8.8% default rate (177/2,000). Applied SMOTE inside the training fold only (never test fold) + `class_weight='balanced'`. Recall improved from 0.107 (no correction) to 0.901.

**Caveat:**
Model trained on 2,000 synthetic records with engineered feature distributions. ROC-AUC of 0.947 reflects synthetic data separability. Production deployment requires minimum 5,000 historical loan records with verified default outcomes.

---

## Data Quality Findings (Part A + B)

| Check | Result |
|---|---|
| credit_score null | **FAILED** — 6 applications (4.6%) |
| annual_income null | **FAILED** — 5 applications (3.8%) |
| loan_id uniqueness | PASSED |
| credit_score range (300–900) | PASSED |
| annual_income > 0 | PASSED |
| loan_status valid values | PASSED |

**Regulatory exposure:** 6 applications had no bureau score — meaning approval decisions were made without the RBI-mandated creditworthiness check. Direct exposure to supervisory action under the Credit Information Companies Regulation Act.

---

## Live API

Flask API deployed via ngrok from Google Colab:

```
POST https://impolite-creamer-reprint.ngrok-free.dev/score
```

**Request payload:**
```json
{
  "loan_id": "LN100234",
  "branch": "Bangalore",
  "credit_score": 510,
  "existing_emis": 4,
  "employment_status": "Unemployed",
  "loan_amount": 1200000,
  "annual_income": 800000,
  "loan_purpose": "Business",
  "loan_tenure_months": 36,
  "applicant_age": 42,
  "branch_manager_email": "manager@finsight.com"
}
```

**Response:**
```json
{
  "loan_id": "LN100234",
  "default_probability": 0.74,
  "risk_tier": "High",
  "flagged": true,
  "alert_text": "This Business loan application for LN100234 is classified as high-risk..."
}
```

> Note: ngrok URL is session-bound to Google Colab runtime. URL changes on each Colab restart.

---

## Deliverables

| # | Deliverable | Folder | Format |
|---|---|---|---|
| D1 | Profiling + GX notebook | /D1 | .ipynb — HTML reports + CFO compliance memo |
| D2 | Classifier + LangChain notebook | /D2 | .ipynb — metrics, class imbalance note, prompt eval, risk_tier column |
| D3 | n8n workflow | /D3 | .json — 6 nodes, Slack + Gmail parallel on True branch |
| D4 | 2 PM Risk Committee Brief | /D4 | .md — 5 sentences, every claim backed by a number |
| D5 | Scored applications CSV | /D5 | .csv — default_probability and risk_tier columns populated |
| D6 | Weekly risk summary | /D6 | .csv + .md — CFO report language (in progress) |
| — | Raw dataset | /Data | finsight_loan_applications.csv |

---

## Repository Structure

```
FinSight/
├── D1/                          # Data audit notebook + GX HTML report
├── D2/                          # Classifier + LangChain notebook
├── D3/                          # n8n workflow JSON
├── D4/                          # Risk committee brief
├── D5/                          # Scored applications CSV
├── D6/                          # Weekly risk summary (in progress)
├── Data/                        # Raw + synthetic datasets
├── Summary/                     # Project summary docs
└── README.md
```

---

## Risk Tier Definition

| Tier | Threshold | Action |
|---|---|---|
| High | ≥ 0.60 | Slack alert + Gmail to branch manager + Sheets log |
| Medium | 0.35 – 0.59 | Sheets log only |
| Low | < 0.35 | Sheets log only |

---

## 2 PM Risk Committee Brief

> "Across 2,000 loan applications reviewed, 6 records had no credit bureau score on file, meaning approval decisions for those loans were made without completing the RBI-mandated creditworthiness check. Hyderabad branches show a 40% high-risk application concentration — nearly double Pune and Kolkata at 22% — suggesting a branch-level underwriting discipline gap. The moment a high-risk application enters the system, it simultaneously triggers a Slack alert to the credit team, an email to the branch manager with specific risk factors, and logs the application to a tracked Google Sheet — all within seconds, before any human has touched the file. If the bank continues without this system, any RBI audit will find that 6 applications were approved without a documented creditworthiness assessment, creating direct exposure to supervisory action under the Credit Information Companies Regulation Act. The metric this committee should review every month is the false negative rate — what percentage of loans the system approved that defaulted within 90 days — because that number tells you whether the 0.3 risk threshold needs recalibration."

---

## Known Limitations & V2 Improvements

### V1 Limitations

**1. Loan-to-income ratio not engineered as a feature.**
The model treats `loan_amount` and `annual_income` as independent signals.
A borrower with credit score 410 requesting 6.7x their annual income is 
classified Low risk because the model never learned the ratio relationship.
V2 will add `loan_to_income = loan_amount / annual_income` as an explicit feature.

**2. Input boundary constraints.**
Model trained on synthetic data with bounded ranges:
- annual_income: ₹1,00,000 – ₹11,55,914
- loan_amount: ₹1,00,000 – ₹11,88,621
- existing_emis: 0 – 6
- applicant_age: 22 – 64
Inputs outside these ranges produce unreliable scores. 
Flask API enforces validation and returns 400 for out-of-range inputs.

**3. Synthetic training data.**
Model trained on 2,000 synthetically generated records.
Real-world performance will differ. Production deployment requires 
minimum 5,000 historical loan records with verified default outcomes.

**4. ngrok URL is session-bound.**
Flask API URL changes on every Colab restart. 
V2 will deploy to Railway.app or Google Cloud Run for a stable endpoint.

### Planned V2 Improvements
- Engineer loan_to_income, debt_service_coverage_ratio as features
- Train on real RBI-published NPA dataset when available
- Deploy Flask API to Railway.app — permanent stable URL
- Add LangSmith observability to trace every LLM alert generation
- Add LangGraph agentic layer for multi-step underwriting decisions

## Author

**Rajan** — Senior Test Architect transitioning to Forward Deployed AI Engineering.
USPTO Patent holder (US11520685) | PMP | AWS Cloud Practitioner

GitHub: [github.com/Rajarajan1087](https://github.com/Rajarajan1087)
