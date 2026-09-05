# ServiceNow Gemini Webhook Service

This FastAPI service receives incident webhooks from ServiceNow and asks Gemini
to decide whether to resolve the incident, request more information, or escalate
it. It writes the resulting message back to the same incident as resolution
notes, a customer-visible comment, or an internal work note.

## Setup

Clone the repository and open its directory:

```powershell
git clone <repository-url>
cd webhook_service
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create the local configuration file from the example and fill in all four
values:

```powershell
Copy-Item .env.example .env
```

`GEMINI_API_KEY` is your Gemini API key. `SN_INSTANCE_URL`, `SN_USERNAME`, and
`SN_PASSWORD` are the URL and Basic Auth credentials for the ServiceNow PDI.
Keep `.env` private; it is excluded from Git.

## Run locally

Start the API:

```powershell
uvicorn main:app --reload --port 8000
```

In another terminal, expose it with ngrok:

```powershell
ngrok http 8000
```

Paste the public ngrok URL plus `/webhook` into the ServiceNow Business Rule.
ngrok normally assigns a new URL whenever it restarts, so update the Business
Rule every time ngrok restarts.

## Test Gemini locally

With `.env` configured, run the three Gemini triage checks:

```powershell
python test_local.py
```

## Test with the ServiceNow PDI

1. Confirm `.env` contains the PDI URL and a ServiceNow account permitted to
   update incidents.
2. Start the API and ngrok using the commands above.
3. Paste the current `https://.../webhook` ngrok address into the ServiceNow
   Business Rule, then save it.
4. Create or update an incident so the Business Rule sends the webhook.
5. Check the incident activity stream: a Gemini response resolves the incident,
   a question appears as a customer-visible comment, and an escalation appears
   as an internal work note.

This test writes to the selected PDI incident. Use a non-production test
incident and verify the close-code choice on that instance before testing a
`respond` decision.
