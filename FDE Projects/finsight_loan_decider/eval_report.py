import joblib
import json
import pandas as pd
from sklearn.model_selection import train_test_split

# --- Load model artifacts ---
model     = joblib.load('ModelArtifacts/calibrated_rf_model.pkl')
encoders  = joblib.load('ModelArtifacts/label_encoders.pkl')

with open('ModelArtifacts/risk_thresholds.json') as f:
    thresholds = json.load(f)

# --- Load clean data ---
df = pd.read_csv('Data/loan_data_clean.csv')

FEATURES = [
    'person_age', 'person_income', 'person_emp_length', 'loan_amnt',
    'loan_int_rate', 'loan_percent_income', 'cb_person_cred_hist_length',
    'cb_person_default_on_file', 'person_home_ownership',
    'loan_intent', 'loan_grade'
]
CATEGORICALS = ['person_home_ownership', 'cb_person_default_on_file', 'loan_grade', 'loan_intent']
TARGET = 'loan_status'

X = df[FEATURES].copy()
y = df[TARGET]

# Apply same label encoders used during training
for col in CATEGORICALS:
    if col in encoders:
        X[col] = encoders[col].transform(X[col])

# Recreate exact same split as training (random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Get predicted probabilities on test set
y_prob = model.predict_proba(X_test)[:, 1]
y_pred = (y_prob >= thresholds['high_threshold']).astype(int)

print(f"Test set size : {len(X_test)} rows")
print(f"Default rate  : {y_test.mean():.1%}")
print(f"High threshold: {thresholds['high_threshold']}")
print(f"Flagged as High Risk: {y_pred.sum()} loans")

# --- Block 3: Confusion Matrix ---
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Predicted: Good', 'Predicted: Default'],
            yticklabels=['Actual: Good',    'Actual: Default'])
plt.title('Confusion Matrix — FinSight Loan Decider')
plt.tight_layout()
plt.savefig('Reports/confusion_matrix.png', dpi=150)
plt.show()
print("Confusion matrix saved to Reports/confusion_matrix.png")
print(f"\nFalse Negatives (missed defaulters) : {cm[1][0]}")
print(f"False Positives (wrongly rejected)  : {cm[0][1]}")

# --- Block 4: ROC Curve ---
from sklearn.metrics import roc_curve, roc_auc_score

fpr, tpr, _ = roc_curve(y_test, y_prob)
auc = roc_auc_score(y_test, y_prob)

plt.figure(figsize=(7, 5))
plt.plot(fpr, tpr, color='steelblue', lw=2, label=f'ROC Curve (AUC = {auc:.3f})')
plt.plot([0, 1], [0, 1], color='grey', linestyle='--', label='Random Guess')
plt.scatter(cm[0][1]/(cm[0][0]+cm[0][1]), cm[1][1]/(cm[1][0]+cm[1][1]),
            color='red', zorder=5, s=100, label=f'Current threshold ({thresholds["high_threshold"]})')
plt.xlabel('False Positive Rate (wrongly rejected good loans)')
plt.ylabel('True Positive Rate (defaulters caught)')
plt.title('ROC Curve — FinSight Loan Decider')
plt.legend()
plt.tight_layout()
plt.savefig('Reports/roc_curve.png', dpi=150)
plt.show()
print(f"\nAUC Score : {auc:.3f}")
print("ROC curve saved to Reports/roc_curve.png")

# --- Block 5: Feature Importance ---
# Extract the Random Forest from inside the calibrated pipeline
rf_model = model.calibrated_classifiers_[0].estimator.named_steps['classifier']
importances = pd.Series(rf_model.feature_importances_, index=FEATURES).sort_values(ascending=True)

plt.figure(figsize=(8, 6))
importances.plot(kind='barh', color='steelblue')
plt.xlabel('Importance Score')
plt.title('Feature Importance — FinSight Loan Decider')
plt.tight_layout()
plt.savefig('Reports/feature_importance.png', dpi=150)
plt.show()
print("\nTop 3 features:")
print(importances.sort_values(ascending=False).head(3))

# --- Block 6: Precision-Recall Curve ---
from sklearn.metrics import precision_recall_curve, average_precision_score

precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_prob)
avg_precision = average_precision_score(y_test, y_prob)
baseline = y_test.mean()

plt.figure(figsize=(7, 5))
plt.plot(recall_vals, precision_vals, color='darkorange', lw=2,
         label=f'PR Curve (AP = {avg_precision:.3f})')
plt.axhline(y=baseline, color='grey', linestyle='--',
            label=f'Random Classifier (baseline = {baseline:.2f})')
plt.scatter(cm[1][1]/(cm[1][0]+cm[1][1]), cm[1][1]/(cm[1][1]+cm[0][1]),
            color='red', zorder=5, s=100, label=f'Current threshold ({thresholds["high_threshold"]})')
plt.xlabel('Recall (defaulters caught)')
plt.ylabel('Precision (how often flag is correct)')
plt.title('Precision-Recall Curve — FinSight Loan Decider')
plt.legend()
plt.tight_layout()
plt.savefig('Reports/precision_recall.png', dpi=150)
plt.show()
print(f"\nAverage Precision : {avg_precision:.3f}")
print(f"Baseline (random) : {baseline:.3f}")
print("Precision-Recall curve saved to Reports/precision_recall.png")
