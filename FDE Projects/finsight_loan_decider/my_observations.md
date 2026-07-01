# FinSight Loan Decider — My Observations

---

## Model Training

- Applied SMOTE oversampling to handle class imbalance in loan default data (~10–20% default rate in real datasets)
- Used `class_weight='balanced'` in RandomForestClassifier alongside SMOTE — both techniques applied together for stronger imbalance handling
- Applied `CalibratedClassifierCV` with sigmoid method to convert raw scores into meaningful probabilities
- Despite all three best practices (SMOTE + balanced weights + calibration), the model still produces bimodal probabilities — confirming the underlying data genuinely separates risk sharply
- Credit risk in real-world data is rarely ambiguous — applicants are either clearly creditworthy or clearly not

---

## Model Behaviour

- Discovered a sharp decision cliff: loan_percent_income at ~0.31 for PERSONAL intent causes probability to jump from 0.33 to 0.94 in a single step
- Loan intent is a dominant feature: MEDICAL, HOMEIMPROVEMENT, EDUCATION → consistently Low risk; PERSONAL, DEBTCONSOLIDATION, VENTURE → consistently High risk
- Loan grade is highly predictive: Grade A/B → Low risk regardless of other factors; Grade C and below → High risk regardless of income
- Medium risk tier (probability 0.30–0.60) exists — 364 cases in test data — but was invisible because deployed thresholds were misconfigured
- The bimodal behaviour is a talking point, not a flaw — it validates that the model learned real credit risk patterns

---

## Deployment (Railway)

- Saving the model without compression produced a 278MB pkl file that triggered Git LFS automatically
- Railway does not pull Git LFS files — it only receives the 134-byte pointer file
- joblib read the LFS pointer and crashed with `KeyError: 118` (ASCII code for 'v' in 'version https://...')
- Spent time chasing Python version mismatches before identifying the real cause as the LFS pointer
- Fix: `joblib.dump(model, path, compress=('lzma', 9))` reduced the file to 22MB — no LFS needed
- Always compress model artifacts before committing to avoid deployment failures

---

## Model Internals

- `CalibratedClassifierCV(cv=3)` trains 3 separate models internally (one per cross-validation fold) — stored under `calibrated_classifiers_`, not `estimators_`
- To extract the Random Forest from inside the calibrated pipeline: `model.calibrated_classifiers_[0].estimator.named_steps['classifier']`
- Feature importances live inside the Random Forest, not on the CalibratedClassifierCV wrapper — you must dig two levels deep to reach them
- Each `calibrated_classifiers_[i]` holds the ImbPipeline (SMOTE → RandomForest) for that fold, plus the sigmoid calibration layer on top

---

## Threshold Configuration

- D2 notebook designed thresholds as `low=0.3, high=0.6` — meaning: below 0.3 → Low, 0.3–0.6 → Medium, above 0.6 → High
- Deployed `risk_thresholds.json` had different values (`medium=0.40, high=0.65`) — causing 364 Medium cases to be misclassified as Low
- Root cause: thresholds were manually set during deployment without checking the D2 notebook values
- Fix: synced `risk_thresholds.json` to `{"medium_threshold": 0.3, "high_threshold": 0.6}` — all 3 tiers now trigger correctly
- Lesson: always save thresholds programmatically from the training notebook, never hardcode them manually during deployment

---

## Flask API

- `loan_percent_income` is computed dynamically from `loan_amnt / person_income` if not passed in request — reduces form complexity
- Field names in the API must exactly match the training feature names (e.g. `loan_amnt` not `loan_amount`, `person_age` not `applicant_age`)
- CORS must be enabled for browser-based clients (GitHub Pages form) to call the Railway API
- Validation rejects inputs outside training distribution ranges to prevent silent bad predictions

---

## LangGraph Agent

- LangGraph agent only invokes when `risk_tier == 'High'` — intentional cost optimisation; calling an LLM for every loan is unnecessary and expensive
- 3-node pipeline: `credit_check → income_verification → decision` — each node adds context for the next
- LangSmith tracing logs every Mistral call — useful for debugging hallucinations or unexpected outputs
- LangGraph replaced a single LangChain RunnableSequence — the multi-step structure produces more specific, actionable alerts
- For a 90.8% default probability loan, the agent correctly identified prior default history, income-to-loan gap, and employment tenure as risk factors

---

## n8n Workflow

- ngrok URLs are temporary — they expire when the local server stops; should never be used as a permanent API endpoint
- n8n Test mode webhook only listens for one event at a time — must click "Listen for test event" before each test
- Field names sent to the n8n webhook must match the Flask API exactly — `{{ $json.body }}` passes them through directly
- Slack bold formatting uses single asterisks: `*text*` — different from Markdown which uses double
- Activating a workflow (Publish) switches from test URL to production URL — the path changes from `/webhook-test/` to `/webhook/`
- n8n cloud trial ends after 14 days — export workflows as JSON immediately to avoid losing work
- The end-to-end flow (Webhook → ML Risk Scorer → IF → Gmail + Slack + Google Sheets) confirms the system works as a real automated risk monitoring pipeline

---

## Feature Importance (from eval_report.py)

- `loan_percent_income` is the #1 most important feature (score 0.203) — the loan-to-income ratio drives the model more than any other signal
- `loan_int_rate` is #2 (score 0.192) — interest rate is a stronger signal than loan grade because Grade C loans inherently carry higher rates; the model learned the rate directly, making grade partially redundant
- `person_income` is #3 (score 0.157) — raw income matters more than the loan grade label assigned by the lender
- `loan_grade` is only #6 (score 0.068) — lower than expected; it is correlated with interest rate and income, so the model extracts the same information from those features directly
- `cb_person_default_on_file` is #11 — last of all features (score 0.010); prior default history is the weakest predictor, showing that current repayment capacity (income, rate, loan ratio) matters more than past behaviour
- The sharp probability cliff we observed at loan_percent_income ~0.31 is explained by it being the top feature — small changes in this ratio cause large shifts in the model's decision
- Portfolio talking point: *"Feature importance revealed that loan_percent_income and interest rate outweigh loan grade and prior default history — suggesting the model learned that current repayment capacity matters more than credit history labels"*

---

## Data & Feature Engineering

- `loan_percent_income` is one of the most powerful features — small changes (0.30 vs 0.32) cause large probability shifts
- The training data's intent distribution explains model behaviour: DEBTCONSOLIDATION and PERSONAL loans default more in real data, so the model learned this pattern correctly
- Inconsistency between loan_grade and loan_int_rate in test inputs (e.g. Grade B with 16% rate) can confuse the model since these are correlated in training data
- Great Expectations validation was set up to catch data quality issues before scoring — important for production pipelines

---

## Architecture Decisions

- Chose Flask over FastAPI for simplicity — appropriate for a portfolio project with a single scoring endpoint
- Chose Railway over Render/Heroku for deployment — faster cold starts, simpler config via environment variables
- Chose n8n cloud over self-hosted for automation — avoids Node.js version compatibility issues (v24 not supported by n8n)
- Chose LangGraph over a single LangChain prompt — multi-step reasoning produces more structured, actionable outputs
- Chose joblib lzma compression over model quantisation — simpler, reversible, and sufficient for this model size
