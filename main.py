# Run with: uvicorn main:app --reload --port 8000
"""Webhook API entry point."""

import logging

from fastapi import BackgroundTasks, FastAPI, status

from gemini_service import get_decision
from models import IncidentPayload


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# This is intentionally process-local. Persistent/cross-worker deduplication is
# a later concern once webhook delivery and ServiceNow write-back are in place.
processed_incident_ids: set[str] = set()


async def triage_incident(payload: IncidentPayload) -> None:
    """Get and log the Gemini triage decision after the webhook response."""
    decision = await get_decision(payload.short_description, payload.description)
    logger.info(
        "Gemini decision for incident %s (%s): %s",
        payload.number,
        payload.incident_sys_id,
        decision,
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
