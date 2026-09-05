# AI Revenue Recovery Agent — Razorpay AI Builder Internship 2026

## Problem
Merchants lose revenue when payments fail due to insufficient funds, bank timeouts, OTP failures, or card declines. Manual follow-up is slow and inconsistent.

## Solution
A multi-agent AI system exposed via REST API that automatically classifies payment failures, decides the appropriate recovery action, generates a personalized customer message, and maintains a full audit trail. Low-confidence cases are flagged for human review instead of guessing.

## Architecture
- Classifier Agent: Categorizes the failure reason from error data
- Decision Agent: Chooses the recovery action based on category
- Messaging Agent: Generates a personalized customer-facing message
- All decisions are logged to audit_log.csv for full auditability

## Tech Stack
Python, Flask (REST API), Pandas

## Run it
pip install flask pandas
python agent.py

Then visit: http://127.0.0.1:5000/run-agent
