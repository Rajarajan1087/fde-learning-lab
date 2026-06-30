# FinSight Loan Decider

**AI-powered loan risk scoring system — built end-to-end from data to production API.**

Live Demo: [finsight-form on GitHub Pages](https://rajarajan1087.github.io/finsight-form/)  
API Endpoint: `https://fde-learning-lab-production.up.railway.app`  
Observability: LangSmith — FinSight_LoanDecider project  
Dataset: [Credit Risk Dataset — Kaggle (laotse)](https://www.kaggle.com/datasets/laotse/credit-risk-dataset)

---

## What This Is

FinSight Loan Decider is a production-deployed machine learning system that predicts the probability a loan applicant will default. It combines a calibrated Random Forest model with a real-time LLM alert system — when a High-risk application is detected, the API automatically generates a human-readable analyst note using Mistral AI via LangChain, and every LLM call is traced in LangSmith.

The system is accessible via a public web form — no technical knowledge required from the end user.

---

## How It Was Built — The Real Story

This is not a notebook project. Each phase produced real output that the next phase consumed.

**Phase 1 — Data + Validation (Google Colab)**  
Loaded the Kaggle dataset (32,581 rows), cleaned missing values, capped outliers, validated with Great Expectations (12 checks, all passed), profiled with ydata-profiling. Saved `loan_data_clean.csv`.

**Phase 2 — Model Training (Google Colab)**  
Trained a Random Forest with SMOTE and sigmoid calibration on the cleaned data. Evaluated on a held-out test set of 6,515 rows (ROC-AUC 0.919). Saved three artifacts to disk: `calibrated_rf_model.pkl`, `label_encoders.pkl`, `risk_thresholds.json`. Scored the full test set and saved `finsight_v2_scored.csv`.

**Phase 3 — LLM Alerts (Google Colab + Mistral AI)**  
Selected the 150 highest-risk records from the scored test set. Sent each to Mistral AI via LangChain, reviewed the output quality, and stored all 150 alerts in `finsight_alerts_final.csv`. This step proved the prompt design and LLM response quality at scale before any API was built.

**Phase 4 — Flask API + Railway Deployment (Local)**  
Built the Flask API that loads the three saved artifacts at startup and serves live scoring via `POST /score`. High-risk requests trigger a real-time Mistral call — the same prompt validated in Phase 3. Deployed to Railway.app with Gunicorn. LangSmith tracing captures every live LLM call. A public web form on GitHub Pages gives non-technical users a browser interface to the same API.

**The key point:** the model was trained once in Colab and the artifacts saved. The Flask API does not retrain — it loads and serves. The D3 pre-generated alerts were the validation gate that confirmed the LLM prompt worked before the API went live.

---

## Architecture

```
User (Web Form)
      │
      ▼
GitHub Pages (HTML Form)
      │  POST /score
      ▼
Flask API — Railway.app (always-on)
      │
      ├── scikit-learn Random Forest → default probability + risk tier
      │
      └── [High risk only] LangChain + Mistral AI → analyst alert text
                                    │
                                    └── LangSmith → trace every LLM call
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | scikit-learn — Calibrated Random Forest |
| Data Balancing | imbalanced-learn (SMOTE) |
| Data Profiling | ydata-profiling |
| Data Validation | Great Expectations |
| API | Flask + Gunicorn |
| LLM Alerts | LangChain + Mistral AI (mistral-small-latest) |
| Observability | LangSmith |
| Deployment | Railway.app |
| Frontend | GitHub Pages (plain HTML/JS) |
| Model Storage | joblib with lzma compression |

---

## Dataset

- **Source:** [Credit Risk Dataset — Kaggle (laotse)](https://www.kaggle.com/datasets/laotse/credit-risk-dataset)
- **Raw rows:** 32,581
- **After cleaning:** 32,574 (7 dropped — age > 80)
- **Default rate:** 21.8% (realistic for retail lending)
- **Features:** 11 (age, income, employment length, home ownership, loan amount, interest rate, loan purpose, loan grade, credit history length, prior default, loan-to-income ratio)

---

## Data Pipeline (D1 — Data Audit)

### Cleaning Steps
- **895 missing values** in `person_emp_length` — filled with median
- **3,116 missing values** in `loan_int_rate` — filled with median grouped by loan grade
- **2 outliers** in `person_emp_length` (value = 123) — capped at 60
- **7 rows** with `person_age` > 80 — dropped
- `cb_person_default_on_file` encoded from Y/N to 1/0
- `loan_id` generated: LN00001 to LN32574

### Great Expectations — 12 Checks, All Passed
| Check | Column | Result |
|---|---|---|
| Not null + Unique | loan_id | PASSED |
| Not null + Range 20–80 | person_age | PASSED |
| Not null + Positive | person_income | PASSED |
| Not null + Range 0–60 | person_emp_length | PASSED |
| Not null + Range 500–35,000 | loan_amnt | PASSED |
| Not null + Range 5–24 | loan_int_rate | PASSED |
| Not null + Range 0–1 | loan_percent_income | PASSED |
| Not null + Positive | cb_person_cred_hist_length | PASSED |
| Valid set {0, 1} | cb_person_default_on_file | PASSED |
| Valid set | person_home_ownership | PASSED |
| Valid set | loan_intent | PASSED |
| Valid set A–G | loan_grade | PASSED |

ydata-profiling report generated and saved for full EDA.

---

## Model (D2 — Classifier)

### Training
- **Train / Test split:** 80/20 stratified (26,059 train / 6,515 test)
- **Algorithm:** Random Forest (`n_estimators=150`) inside an imbalanced-learn pipeline
- **Class imbalance:** SMOTE applied inside the pipeline on training data only
- **Calibration:** `CalibratedClassifierCV` with sigmoid method (Platt scaling)

### Performance on Test Set (6,515 rows)

| Metric | Value |
|---|---|
| Accuracy | 0.912 |
| Precision | 0.862 |
| Recall | 0.711 |
| F1 Score | 0.779 |
| ROC-AUC | 0.919 |

### Threshold Decision
Default threshold of 0.5 gives Recall 0.711. Threshold lowered to 0.3 → Recall 0.763, Precision 0.750.
In credit risk, missing a real defaulter means principal loss — so higher recall at acceptable precision is preferred.

### Risk Tier Distribution (Test Set)
| Tier | Count |
|---|---|
| Low | 5,069 |
| High | 1,082 |
| Medium | 364 |

### Feature Importance (Top 5)
| Feature | Importance |
|---|---|
| loan_percent_income | 20.4% |
| loan_int_rate | 19.0% |
| person_income | 15.7% |
| person_emp_length | 7.9% |
| loan_amnt | 7.4% |

**Key insight:** Loan-to-income ratio and interest rate are the two strongest predictors — not income alone. This is why a high-income applicant with a short credit history requesting the maximum loan amount can still score as high risk.

---

## LLM Alert System (D3 — Alerts)

### What It Does
High-risk applications trigger a Mistral AI call via LangChain. The model receives the applicant profile and writes a 3-sentence internal credit analyst note that:
- States the risk tier and loan purpose with specific concerns
- Identifies the two most alarming factors with actual numbers
- Recommends one specific action before approval

### What Was Built in D3
- 150 High-risk records selected from the scored test set
- Mistral AI (`mistral-small-latest`) alert generated for each
- All 150 alerts stored in `Data/finsight_alerts_final.csv`
- LangSmith tracing enabled from the start — every call logged with input, output, latency, and token count

**Why LLM alerts instead of rule-based messages:**
A rule-based system generates the same text for similar profiles. The LLM produces specific, contextualised language that reads like an analyst wrote it — mentioning the actual numbers and the combination of factors unique to each applicant.

---

## Data Files

| File | Description |
|---|---|
| `Data/loan_data.csv` | Raw Kaggle dataset — 32,581 rows |
| `Data/loan_data_clean.csv` | Cleaned dataset — 32,574 rows |
| `Data/finsight_v2_scored.csv` | Test set (6,515 rows) with default probability and risk tier |
| `Data/finsight_high_risk_with_alerts.csv` | 150 High-risk records with Mistral AI alert text |
| `Data/finsight_alerts_final.csv` | Final 150 alerts — used to validate LLM output quality |

---

## API (D4 — Flask API)

### `GET /health`
Returns service status.
```json
{"status": "online", "service": "FinSight_LoanDecider"}
```

### `POST /score`

**Request fields:**

| Field | Type | Description |
|---|---|---|
| `person_age` | int | Applicant age (20–80) |
| `person_income` | float | Annual income in USD |
| `person_emp_length` | float | Years employed |
| `person_home_ownership` | string | RENT / OWN / MORTGAGE / OTHER |
| `loan_amnt` | float | Loan amount (500–35,000) |
| `loan_int_rate` | float | Interest rate % (5–24) |
| `loan_intent` | string | PERSONAL / EDUCATION / MEDICAL / VENTURE / HOMEIMPROVEMENT / DEBTCONSOLIDATION |
| `loan_grade` | string | A–G |
| `cb_person_cred_hist_length` | float | Credit history in years |
| `cb_person_default_on_file` | int | Prior default: 0 = No, 1 = Yes |

**Response:**
```json
{
  "loan_id": "APP-001",
  "default_probability": 0.908,
  "risk_tier": "High",
  "flagged": true,
  "alert_text": "This application falls into the highest risk tier..."
}
```

### Risk Thresholds
| Tier | Probability Range |
|---|---|
| Low | < 0.40 |
| Medium | 0.40 – 0.65 |
| High | > 0.65 |

---

## Deployment Notes

- **Platform:** Railway.app with Railpack (Python 3.14)
- **Process:** Gunicorn with sync workers
- **CORS:** flask-cors enabled — required for browser-based clients on different domains
- **Secrets:** MISTRAL_API_KEY, LANGCHAIN_API_KEY set via Railway Variables tab — never committed to git
- **Auto-deploy:** Every push to main triggers Railway redeploy
- **Model size:** 22 MB (compressed from 278 MB using lzma)

---

## What I Would Say To...

### Credit Risk Analyst / Risk Team

*"The model scores each application on ten factors — income, employment history, credit history length, loan-to-income ratio, prior defaults, and more. It outputs a probability between 0 and 1 that the applicant will default, mapped to Low, Medium, or High risk tiers. For every High-risk application, the system writes an analyst note that flags the two most concerning factors with the actual numbers — so the reviewer does not have to read through the full profile manually. The thresholds are tunable — if the business wants to be more conservative, we raise the Medium threshold. In our test set of 6,515 applications, the model achieved 91.2% accuracy and 0.919 ROC-AUC."*

### Direct Manager / Team Lead

*"This is a deployed end-to-end ML system — not a notebook. It runs on Railway as a REST API, callable from any system, with a web form so non-technical stakeholders can use it directly. The model was trained on 32,574 cleaned records from a real Kaggle credit risk dataset, uses probability calibration so the scores are meaningful, and handles class imbalance with SMOTE. LangSmith gives us observability on every LLM call — latency, token usage, and the exact prompt and response are all logged and searchable. Data quality was validated with Great Expectations — 12 checks, all passed before training."*

### Senior Manager / Head of Department

*"We have built a loan risk scoring capability that can be integrated into any existing workflow via API. A credit officer fills in the application details, the system scores it in under two seconds, and if it is high risk, it generates a written summary of the key concerns. The model is live in production at a permanent public URL. The architecture is modular — the scoring model and the alert generation are independent, so either can be updated without touching the other. We already generated and validated 150 LLM alert notes on real high-risk records from the test set before going live."*

### CTO / Technical Leadership

*"The system uses a Calibrated Random Forest — calibration matters because we use the probability directly for tiering, not just the binary prediction, so well-calibrated probabilities are critical. The model is serialised with lzma compression (278 MB to 22 MB) and stored as a regular git object — no LFS, no external model registry dependency. The LLM layer uses LangChain's RunnableSequence with LangSmith tracing — every inference is logged with input, output, latency, and token count. CORS is handled at the Flask layer, secrets are Railway environment variables, and the form is statically hosted on GitHub Pages — zero frontend infrastructure cost. The next planned layer is LangGraph to replace the simple chain with a multi-step agent — credit bureau check tool, income verification tool, and decision tool with memory across steps."*

### CFO / Business Leadership

*"This system automates the initial risk triage for loan applications. Instead of a credit officer spending time reading each application before deciding whether to escalate, the system scores it instantly and only escalates the High-risk ones with a written summary already prepared — reducing manual review time per application. Scoring criteria are consistent across every case, and there is a full audit trail of every AI-generated note via LangSmith. The infrastructure cost is minimal — Railway for the API, GitHub Pages for the frontend, and the LLM cost per High-risk alert is a fraction of a cent. In our test set, the model correctly identified 71% of all defaulters (Recall 0.711) with 86% precision."*

---

## Honest Limitations

- The dataset is from Kaggle and is intended for ML practice — model performance on a real bank's loan portfolio would need validation before production use in a regulated environment
- The auto-calculated loan grade in the web form is a simplified heuristic — in a real system this would come from the lender's internal grading engine
- Random Forest decision boundaries can be sharp — a small change in interest rate near a threshold can flip the risk tier. A production system would benefit from a borderline band for ambiguous cases
- No authentication on the API — suitable for demo purposes; production deployment would require API key validation

---

## Lessons Learned

1. **Always compress ML models before committing** — `joblib.dump(model, path, compress=('lzma', 9))` reduced 278 MB to 22 MB. Git LFS on Railway gives you a pointer file, not the model — causing a cryptic `KeyError: 118` on load.

2. **Calibration matters for risk scoring** — a raw Random Forest gives poorly calibrated probabilities. `CalibratedClassifierCV` with sigmoid method makes the output meaningful: 70% probability means 70% likely to default.

3. **CORS must be explicitly enabled** — browser clients on a different domain are blocked by the browser's same-origin policy. `flask-cors` with `CORS(app)` is a one-line fix.

4. **LangSmith from day one** — instrumenting LangChain calls from the start gives latency, cost, and debugging data with no extra code. Adding observability after the fact is harder.

5. **Rule-based grades and ML scores can disagree — and the ML is usually right** — a simple heuristic assigns Grade E to a high-income applicant with a short credit history. The model correctly sees the short history and maximum loan amount as the real risk signals, independent of income.

6. **High income alone does not mean low risk** — loan_percent_income (20.4%) and loan_int_rate (19.0%) are the top two predictors. Income (15.7%) ranks third. A high earner borrowing the maximum at high interest with 1 year of credit history is genuinely high risk.

7. **Threshold selection is a business decision** — the default 0.5 threshold gave Recall 0.711. Lowering to 0.3 raised Recall to 0.763. In credit risk, missing a defaulter costs principal loss, so higher recall at acceptable precision is preferred.

---

## What's Next (Roadmap)

- [ ] **LangGraph agent (in progress — target 2026-07-01)** — replace the simple LangChain chain with a multi-step LangGraph agent: credit check tool, income verification tool, decision tool with memory across steps
- [ ] n8n workflow — connect Railway API to automated notification pipeline
- [ ] Weekly risk summary report with matplotlib
- [ ] Authentication layer on the API
- [ ] Borderline risk tier for ambiguous cases near thresholds

---

*Built as part of the FDE (Financial Data Engineering) learning programme.*
