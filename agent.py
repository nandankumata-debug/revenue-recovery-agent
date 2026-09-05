import pandas as pd
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# ---- Simulated failed transactions (stand-in for Razorpay webhook data) ----
SIMULATED_FAILURES = [
    {"transaction_id": "txn_001", "amount": 1499, "error_description": "Insufficient funds in account"},
    {"transaction_id": "txn_002", "amount": 899,  "error_description": "Payment gateway timeout"},
    {"transaction_id": "txn_003", "amount": 2500, "error_description": "OTP verification failed"},
    {"transaction_id": "txn_004", "amount": 599,  "error_description": "Card declined by issuing bank"},
    {"transaction_id": "txn_005", "amount": 3200, "error_description": "Insufficient balance"},
    {"transaction_id": "txn_006", "amount": 1200, "error_description": "Network error, please retry"},
    {"transaction_id": "txn_007", "amount": 750,  "error_description": "Unusual server response code 9999"},
    {"transaction_id": "txn_008", "amount": 4500, "error_description": "Bank server not responding"},
]

# ---- Rule-based classifier ----
def classify_failure(error_description):
    desc = error_description.lower()
    if "insufficient" in desc or "balance" in desc:
        return "insufficient_funds", 0.95
    elif "timeout" in desc or "server not responding" in desc or "network" in desc:
        return "bank_timeout", 0.9
    elif "otp" in desc:
        return "otp_failed", 0.9
    elif "declined" in desc:
        return "card_declined", 0.85
    else:
        return "unknown", 0.3

# ---- Decide recovery action ----
def decide_action(category, confidence):
    if confidence < 0.5:
        return "flag_for_human_review", "Low classification confidence — escalating instead of guessing."

    actions = {
        "insufficient_funds": ("schedule_retry_24h", "Funds likely unavailable now; retry after 24h with a reminder message."),
        "bank_timeout": ("retry_immediate", "Transient gateway issue; safe to retry immediately."),
        "otp_failed": ("send_new_payment_link", "OTP expired/failed; generate a fresh checkout link for the customer."),
        "card_declined": ("suggest_alt_payment", "Card declined; prompt customer to try another payment method."),
    }
    return actions.get(category, ("flag_for_human_review", "Unrecognized category — needs manual check."))

# ---- Generate a personalized customer message ----
def generate_customer_message(category, amount):
    messages = {
        "insufficient_funds": f"Hi! Your payment of ₹{amount} didn't go through due to insufficient balance. We'll retry in 24 hours — no action needed.",
        "bank_timeout": f"Hi! Your payment of ₹{amount} faced a temporary bank delay. We're retrying it now automatically.",
        "otp_failed": f"Hi! Your OTP verification failed for ₹{amount}. Here's a fresh payment link to complete your purchase.",
        "card_declined": f"Hi! Your card was declined for ₹{amount}. Please try an alternate payment method to complete your order.",
        "unknown": f"We noticed an issue with your ₹{amount} payment. Our team is reviewing it and will follow up shortly."
    }
    return messages.get(category, messages["unknown"])

# ---- Run the agent over all failures and build audit trail ----
def run_agent():
    audit_log = []

    for txn in SIMULATED_FAILURES:
        category, confidence = classify_failure(txn["error_description"])
        action, reasoning = decide_action(category, confidence)
        customer_msg = generate_customer_message(category, txn["amount"])

        record = {
            "timestamp": datetime.now().isoformat(),
            "transaction_id": txn["transaction_id"],
            "amount": txn["amount"],
            "error_description": txn["error_description"],
            "category": category,
            "confidence": confidence,
            "action_taken": action,
            "reasoning": reasoning,
            "customer_message": customer_msg
        }
        audit_log.append(record)

        print(f"\n--- Processing {txn['transaction_id']} (₹{txn['amount']}) ---")
        print(f"Error: {txn['error_description']}")
        print(f"Classified as: {category} (confidence: {confidence})")
        print(f"Action: {action}")
        print(f"Reasoning: {reasoning}")
        print(f"Customer message: {customer_msg}")

    df = pd.DataFrame(audit_log)
    df.to_csv("audit_log.csv", index=False)

    print("\n\n========== SUMMARY REPORT ==========")
    print(f"Total failures processed: {len(df)}")
    print(f"Flagged for human review: {len(df[df['action_taken'] == 'flag_for_human_review'])}")
    print(f"Recovery actions attempted: {len(df[df['action_taken'] != 'flag_for_human_review'])}")
    print("\nFull audit trail saved to audit_log.csv")

    return audit_log

# ---- REST API endpoint ----
@app.route('/run-agent', methods=['GET'])
def api_run_agent():
    results = run_agent()
    return jsonify({
        "status": "success",
        "message": "Agent processed all failures, see audit_log.csv",
        "total_processed": len(results),
        "results": results
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Revenue Recovery Agent API is running. Go to /run-agent to trigger it."})

if __name__ == "__main__":
    app.run(port=5000, debug=True)