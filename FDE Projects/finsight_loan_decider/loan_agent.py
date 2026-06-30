import os
from typing import TypedDict
from langchain_mistralai import ChatMistralAI
from langgraph.graph import StateGraph, START, END

llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=os.environ.get('MISTRAL_API_KEY'),
    temperature=0.35
)


class LoanState(TypedDict):
    loan_data: dict
    ml_probability: float
    credit_assessment: str
    income_assessment: str
    alert_text: str


def credit_check_node(state: LoanState) -> dict:
    d = state["loan_data"]
    default_label = "Yes" if d["cb_person_default_on_file"] == 1 else "No"
    prompt = (
        f"You are a credit analyst. In 2 sentences, assess the credit profile of this applicant.\n"
        f"Focus only on these factors:\n"
        f"- Loan grade: {d['loan_grade']}\n"
        f"- Prior default on file: {default_label}\n"
        f"- Credit history length: {d['cb_person_cred_hist_length']} years\n"
        f"- Interest rate: {d['loan_int_rate']}%\n\n"
        f"Be specific. Use the actual numbers. Plain prose only — no bullet points, no bold."
    )
    response = llm.invoke(prompt)
    return {"credit_assessment": response.content}


def income_verification_node(state: LoanState) -> dict:
    d = state["loan_data"]
    lpi_pct = round(d["loan_percent_income"] * 100, 1)
    prompt = (
        f"You are a credit analyst. In 2 sentences, assess the income and repayment capacity of this applicant.\n"
        f"Focus only on these factors:\n"
        f"- Annual income: ${int(d['person_income']):,}\n"
        f"- Loan amount requested: ${int(d['loan_amnt']):,}\n"
        f"- Loan as % of income: {lpi_pct}%\n"
        f"- Employment length: {d['person_emp_length']} years\n"
        f"- Home ownership: {d['person_home_ownership']}\n\n"
        f"Prior credit note for context: {state['credit_assessment']}\n\n"
        f"Be specific. Use the actual numbers. Plain prose only — no bullet points, no bold."
    )
    response = llm.invoke(prompt)
    return {"income_assessment": response.content}


def decision_node(state: LoanState) -> dict:
    d = state["loan_data"]
    prob_pct = round(state["ml_probability"] * 100, 1)
    prompt = (
        f"You are a senior credit analyst writing an internal alert for the branch manager.\n\n"
        f"The risk model scored this {d['loan_intent']} loan application at {prob_pct}% default probability — High Risk.\n\n"
        f"Credit assessment: {state['credit_assessment']}\n"
        f"Income assessment: {state['income_assessment']}\n\n"
        f"Write exactly 3 sentences:\n"
        f"- Sentence 1: State the risk level and loan purpose, and the single most concerning factor\n"
        f"- Sentence 2: Cite specific numbers from both assessments above\n"
        f"- Sentence 3: Recommend one concrete action before approval\n\n"
        f"Rules: plain prose only, no bullet points, no bold, no asterisks, 100 words max.\n"
        f"Do NOT use the words: model, algorithm, AI.\n"
        f"Do not start with 'Alert' or any label — begin with a regular English word."
    )
    response = llm.invoke(prompt)
    return {"alert_text": response.content}


def build_loan_agent():
    graph = StateGraph(LoanState)
    graph.add_node("credit_check", credit_check_node)
    graph.add_node("income_verification", income_verification_node)
    graph.add_node("decision", decision_node)
    graph.add_edge(START, "credit_check")
    graph.add_edge("credit_check", "income_verification")
    graph.add_edge("income_verification", "decision")
    graph.add_edge("decision", END)
    return graph.compile()


loan_agent = build_loan_agent()
