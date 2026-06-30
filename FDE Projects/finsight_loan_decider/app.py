import os
import json
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- 1. Load Model Artifacts ---
BASE_PATH = 'ModelArtifacts'
model = joblib.load(os.path.join(BASE_PATH, 'calibrated_rf_model.pkl'))
encoders = joblib.load(os.path.join(BASE_PATH, 'label_encoders.pkl'))

with open(os.path.join(BASE_PATH, 'risk_thresholds.json'), 'r') as f:
    thresholds = json.load(f)

# Exact feature order the model was trained on (D2 notebook)
TRAINING_FEATURES = [
    'person_age', 'person_income', 'person_emp_length', 'loan_amnt',
    'loan_int_rate', 'loan_percent_income', 'cb_person_cred_hist_length',
    'cb_person_default_on_file', 'person_home_ownership',
    'loan_intent', 'loan_grade'
]

CATEGORICAL_COLS = ['person_home_ownership', 'cb_person_default_on_file', 'loan_grade', 'loan_intent']

VALID_HOME_OWNERSHIP = {'RENT', 'OWN', 'MORTGAGE', 'OTHER'}
VALID_LOAN_INTENT = {'PERSONAL', 'EDUCATION', 'MEDICAL', 'VENTURE', 'HOMEIMPROVEMENT', 'DEBTCONSOLIDATION'}
VALID_LOAN_GRADE = {'A', 'B', 'C', 'D', 'E', 'F', 'G'}

# --- 2. Initialize LLM ---
llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=os.environ.get('MISTRAL_API_KEY'),
    temperature=0.35
)

# --- 3. Prompt Template for Alerts ---
# loan_id included so Mistral knows which application it is writing about (matches D3/D4 notebooks)
ALERT_VARIABLES = [
    "loan_id", "person_age", "person_income", "person_emp_length", "loan_amnt",
    "loan_int_rate", "loan_percent_income", "cb_person_cred_hist_length",
    "cb_person_default_on_file", "person_home_ownership", "loan_intent", "loan_grade"
]

alert_template = PromptTemplate(
    input_variables=ALERT_VARIABLES,
    template="""
You are a senior credit analyst at FinSight Capital writing an internal note.

Write a 3-sentence alert for the branch manager:
- Sentence 1: State the risk tier and loan purpose, explain why this application is concerning
- Sentence 2: Identify the two most concerning factors with specific numbers
- Sentence 3: Recommend one specific action before approval

Applicant Profile:
- Loan ID: {loan_id}
- Age: {person_age} years old
- Annual Income: ${person_income} | Employment Experience: {person_emp_length} years
- Home Ownership: {person_home_ownership}
- Credit History Length: {cb_person_cred_hist_length} years
- Default Status: {cb_person_default_on_file}
- Loan Amount: ${loan_amnt} | Purpose: {loan_intent} | Interest Rate: {loan_int_rate}% | Percent Income: {loan_percent_income}%
- Loan Grade: {loan_grade}

Rules:
- Do NOT use the words: model, algorithm, AI
- Write in flowing prose, no bullet points, no bold headers
- Write exactly 3 sentences
- 100 words maximum
- Read like a human credit analyst note
- Write in plain text only — no asterisks, no bold, no italic, no headers
- Do not start with "Alert" or "Credit Alert" or any label
- First word must be a regular English word starting the first sentence directly
"""
)

alert_chain = alert_template | llm


def validate_input(data):
    errors = []

    required = [
        'person_age', 'person_income', 'person_emp_length',
        'person_home_ownership', 'cb_person_cred_hist_length',
        'cb_person_default_on_file', 'loan_amnt', 'loan_intent',
        'loan_int_rate', 'loan_grade'
    ]
    missing = [f for f in required if f not in data]
    if missing:
        return [f'Missing required field: {f}' for f in missing]

    if not (20 <= data['person_age'] <= 80):
        errors.append('person_age must be between 20 and 80')
    if not (8000 <= data['person_income'] <= 271268):
        errors.append('person_income must be between 8,000 and 271,268')
    if not (500 <= data['loan_amnt'] <= 35000):
        errors.append('loan_amnt must be between 500 and 35,000')
    if not (5 <= data['loan_int_rate'] <= 24):
        errors.append('loan_int_rate must be between 5 and 24')
    if data['cb_person_default_on_file'] not in (0, 1):
        errors.append('cb_person_default_on_file must be 0 or 1')
    if data['person_home_ownership'] not in VALID_HOME_OWNERSHIP:
        errors.append(f'person_home_ownership must be one of {sorted(VALID_HOME_OWNERSHIP)}')
    if data['loan_intent'] not in VALID_LOAN_INTENT:
        errors.append(f'loan_intent must be one of {sorted(VALID_LOAN_INTENT)}')
    if data['loan_grade'] not in VALID_LOAN_GRADE:
        errors.append(f'loan_grade must be one of {sorted(VALID_LOAN_GRADE)}')

    return errors


# --- 4. API Routes ---
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'online', 'service': 'FinSight_LoanDecider'})

@app.route('/score', methods=['POST'])
def score():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid or missing JSON body'}), 400

        errors = validate_input(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400

        # Compute loan_percent_income dynamically if not provided
        if 'loan_percent_income' not in data:
            data['loan_percent_income'] = round(data['loan_amnt'] / data['person_income'], 4)

        # Build DataFrame aligned to exact training feature order; rejects unknown fields
        input_df = pd.DataFrame([{feat: data[feat] for feat in TRAINING_FEATURES}])

        # Apply Label Encoders
        for col in CATEGORICAL_COLS:
            if col in encoders:
                input_df[col] = encoders[col].transform(input_df[col])

        # Predict default probability
        prob = model.predict_proba(input_df)[0][1]

        # Map probability to risk tier
        tier = 'Low'
        if prob >= thresholds['high_threshold']:
            tier = 'High'
        elif prob >= thresholds['medium_threshold']:
            tier = 'Medium'

        # Generate LLM alert for High-risk applications
        # person_income and loan_amnt formatted with commas to match D3/D4 notebooks
        alert_text = ""
        if tier == 'High':
            alert_payload = {
                "loan_id": data.get('loan_id', 'N/A'),
                "person_age": data['person_age'],
                "person_income": f"{int(data['person_income']):,}",
                "person_emp_length": data['person_emp_length'],
                "loan_amnt": f"{int(data['loan_amnt']):,}",
                "loan_int_rate": data['loan_int_rate'],
                "loan_percent_income": data['loan_percent_income'],
                "cb_person_cred_hist_length": data['cb_person_cred_hist_length'],
                "cb_person_default_on_file": data['cb_person_default_on_file'],
                "person_home_ownership": data['person_home_ownership'],
                "loan_intent": data['loan_intent'],
                "loan_grade": data['loan_grade'],
            }
            alert_response = alert_chain.invoke(alert_payload)
            alert_text = alert_response.content

        return jsonify({
            'loan_id': data.get('loan_id'),
            'default_probability': round(float(prob), 3),
            'risk_tier': tier,
            'flagged': tier == 'High',
            'alert_text': alert_text
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
