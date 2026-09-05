# ServiceNow Gemini Webhook Service

This FastAPI service receives new ServiceNow incidents and asks Gemini whether
to resolve them, ask the customer for more information, or escalate them. It
writes the resulting message back to the same incident.

## Demo Video

[Watch the demo video](https://drive.google.com/file/d/1aYW4mKz6hJeUvDAuPu6ftOSGVe4FW9Sk/view?usp=sharing)

## Setup

Clone the repository and open it:

```powershell
git clone https://github.com/ahmedtamer101/Sprints-Task-0.git
cd Sprints-Task-0
```

Install the dependencies with Python 3.11+:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` from the template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` so it has this format, replacing the placeholder values with your
own credentials:

```makefile
GEMINI_API_KEY=
SN_INSTANCE_URL=https://devXXXXXX.service-now.com
SN_USERNAME=admin
SN_PASSWORD=
```

Put real secrets only in `.env`, never in `.env.example`. `.env` is
gitignored and must remain private.

## Run the service and create a public tunnel

Start FastAPI:

```powershell
python -m uvicorn main:app --reload --port 8000
```

Download the Windows `cloudflared` executable and either place it on your
`PATH` or keep it in Downloads. Start a Cloudflare Quick Tunnel in another
terminal:

```powershell
cloudflared tunnel --protocol http2 --url http://localhost:8000
```

If you run the executable directly from Downloads, use:

```powershell
.\cloudflared-windows-amd64.exe tunnel --protocol http2 --url http://localhost:8000
```

The command prints a temporary `https://...trycloudflare.com` URL. Keep the
tunnel running, and update the ServiceNow Business Rule whenever that URL
changes.

## Configure the ServiceNow Business Rule

Create a Business Rule with these values:

- Name: `Task0 - Send Incident to Agent`
- Table: `Incident [incident]`
- Active: checked
- Advanced: checked
- When: `after`
- Insert: checked
- Update, Delete, and Query: unchecked

In the **Script** field, paste the following `business_rule.js` content. Replace
only `YOUR_ENDPOINT` with the current Cloudflare Quick Tunnel URL and keep the
`/webhook` suffix.

```javascript
(function executeRule(current, previous) {
    var request = new sn_ws.RESTMessageV2();
    request.setEndpoint("YOUR_ENDPOINT/webhook");
    request.setHttpMethod("post");
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestBody(JSON.stringify({
        incident_sys_id: current.getUniqueValue(),
        number: current.getValue("number"),
        short_description: current.getValue("short_description"),
        description: current.getValue("description") || "",
        priority: current.getValue("priority")
    }));
    request.execute();
})(current, previous);
```

This script sends exactly these fields: `incident_sys_id`, `number`,
`short_description`, `description`, and `priority`. Save the Business Rule.

## Run local Gemini tests

With `.env` configured, run:

```powershell
python test_local.py
```

All three cases should report `PASS`.

## Test with the ServiceNow PDI

1. Confirm `.env` has the PDI URL and ServiceNow credentials that can update
   incidents.
2. Start FastAPI and the Cloudflare Quick Tunnel, then update the Business Rule
   endpoint with the current tunnel URL.
3. Create a new PDI incident. The insert Business Rule sends it to the service.
4. Check the incident activity after processing: a response resolves it, a
   question is a customer-visible comment, and an escalation is an internal
   work note.

This test changes the selected PDI incident; use a non-production test record.
For the `respond` branch, this PDI uses `Solution provided` as the valid
`close_code` value.

## Screenshots

### Business Rule Setup

![Business Rule configuration](<screenshots/01_business rule config.png>)

![Business Rule script](<screenshots/02_business rule script.png>)

### Respond, Before and After

![Respond before](<screenshots/03_respond before.png>)

![Respond after](<screenshots/04_responed after.png>)

![Respond after notes](<screenshots/05_responed notes.png>)

### Ask, Before and After

![Ask before](<screenshots/06_ask before.png>)

![Ask after](<screenshots/07_ask after.png>)

![Ask after notes](<screenshots/08_ask after notes.png>)

### Escalate, Before and After

![Escalate before](<screenshots/09_ escalate before.png>)

![Escalate after](<screenshots/10_ escalate after.png>)

![Escalate after notes](<screenshots/11_ escalate after notes.png>)
