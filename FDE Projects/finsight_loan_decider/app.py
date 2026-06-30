import os
import json
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from loan_agent import loan_agent

load_dotenv()

app = Flask(__name__)
CORS(app)

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

        # Generate LLM alert for High-risk applications via LangGraph agent
        credit_assessment = ""
        income_assessment = ""
        alert_text = ""
        if tier == 'High':
            result = loan_agent.invoke({
                "loan_data": data,
                "ml_probability": float(prob),
                "credit_assessment": "",
                "income_assessment": "",
                "alert_text": ""
            })
            credit_assessment = result["credit_assessment"]
            income_assessment = result["income_assessment"]
            alert_text = result["alert_text"]

        return jsonify({
            'loan_id': data.get('loan_id'),
            'default_probability': round(float(prob), 3),
            'risk_tier': tier,
            'flagged': tier == 'High',
            'credit_assessment': credit_assessment,
            'income_assessment': income_assessment,
            'alert_text': alert_text
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
