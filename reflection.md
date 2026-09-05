# Reflection

## What was the hardest part?

The hardest part was making the decision logic behave correctly for the vague email ticket. The ticket clearly matched the email topic, but it did not contain enough detail to apply the knowledge-base fix confidently, so the correct decision was `ask` rather than `respond`. The first live Gemini test returned `respond`, which showed me that structured JSON output can guarantee the response format but not the correctness of the decision itself. I had to refine the structured-output guidance while keeping the original prompt unchanged, then retest all three cases until they produced the expected decisions.

The ServiceNow integration was also challenging. I had to debug the Business Rule, the public tunnel, the ServiceNow instance URL, and the write-back fields before the full loop worked correctly. This helped me understand how the webhook, API calls, background processing, and ServiceNow REST API connect together in a real system.

## What would you improve with more time?

With more time, I would improve reliability and testing. The temporary Cloudflare tunnel can disconnect or change its URL, so I would use a more stable deployment or named tunnel for a more reliable integration. I would also add more automated tests for ambiguous tickets, malformed payloads, duplicate requests, and ServiceNow API failures.

I would especially test the `respond`, `ask`, and `escalate` decisions with a larger set of examples to make sure the logic remains consistent beyond the three provided test incidents.
