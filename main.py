# Run with: uvicorn main:app --reload --port 8000
"""Webhook API entry point."""

import logging

from fastapi import BackgroundTasks, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from gemini_service import get_decision
from models import IncidentPayload
from servicenow_service import add_customer_comment, add_work_note, resolve_incident


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# This is intentionally process-local. Persistent/cross-worker deduplication is
# a later concern once webhook delivery and ServiceNow write-back are in place.
processed_incident_ids: set[str] = set()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return actionable validation details for malformed webhook payloads."""
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "Invalid webhook payload",
            "message": (
                "Send JSON with incident_sys_id, number, short_description, and "
                "priority. description is optional."
            ),
            "details": details,
        },
    )


async def triage_incident(payload: IncidentPayload) -> None:
    """Triage an incident and write the resulting action back to ServiceNow."""
    try:
        result = await get_decision(payload.short_description, payload.description)
        logger.info(
            "Gemini decision for incident %s (%s): %s",
            payload.number,
            payload.incident_sys_id,
            result,
        )

        decision = result["decision"]
        message = result["message"]
        if decision == "respond":
            await resolve_incident(payload.incident_sys_id, message)
        elif decision == "ask":
            await add_customer_comment(payload.incident_sys_id, message)
        elif decision == "escalate":
            await add_work_note(payload.incident_sys_id, message)
    except Exception:
        logger.exception(
            "Unexpected background triage failure for incident %s (%s)",
            payload.number,
            payload.incident_sys_id,
        )


@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook(
    payload: IncidentPayload, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Accept a new incident and queue its asynchronous triage."""
    if payload.incident_sys_id in processed_incident_ids:
        logger.info("Ignoring duplicate incident webhook: %s", payload.incident_sys_id)
        return {"status": "duplicate"}

    # Add before scheduling work so near-simultaneous duplicate requests cannot
    # both enqueue a Gemini call.
    processed_incident_ids.add(payload.incident_sys_id)
    background_tasks.add_task(triage_incident, payload)
    return {"status": "accepted"}
