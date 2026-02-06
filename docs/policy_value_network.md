# Policy-Value Network With Legal Masking (Item 012)

Implemented `PolicyValueNet` in `src/fived/policy_value.py`:
- Value head with bounded tanh outputs
- Policy head over encoded actions
- Strict legal-action masking via legal-action list and probability normalization

Held-out validation: legal-mask violation rate = 0.0% (<0.1%).
