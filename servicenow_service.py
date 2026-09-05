"""ServiceNow incident write-back operations."""

import logging
from urllib.parse import quote

import httpx

from config import SN_INSTANCE_URL, SN_PASSWORD, SN_USERNAME


logger = logging.getLogger(__name__)

_INCIDENT_ENDPOINT = "/api/now/table/incident"
_TIMEOUT_SECONDS = 15.0


async def _update_incident(incident_sys_id: str, fields: dict[str, str | int]) -> None:
    """PATCH an incident, containing all downstream HTTP failures."""
    incident_id = quote(incident_sys_id, safe="")
    url = f"{SN_INSTANCE_URL.rstrip('/')}{_INCIDENT_ENDPOINT}/{incident_id}"

    try:
        async with httpx.AsyncClient(
            auth=httpx.BasicAuth(SN_USERNAME, SN_PASSWORD),
            headers={"Content-Type": "application/json"},
            timeout=_TIMEOUT_SECONDS,
        ) as client:
            response = await client.patch(url, json=fields)
            response.raise_for_status()
    except Exception:
        # Do not include the URL or request contents: they can contain instance
        # details or ticket text, respectively. The incident ID is safe for
        # correlating this failure with the webhook request.
        logger.exception("ServiceNow write-back failed for incident %s", incident_sys_id)


async def resolve_incident(incident_sys_id: str, solution_text: str) -> None:
    """Record a solution and resolve an incident in ServiceNow."""
    await _update_incident(
        incident_sys_id,
        {
            "work_notes": solution_text,
            "close_notes": solution_text,
            "state": 6,
            "close_code": "Solution provided",
        },
    )


async def add_customer_comment(incident_sys_id: str, question_text: str) -> None:
    """Add a customer-visible comment requesting more information."""
    await _update_incident(incident_sys_id, {"comments": question_text})


async def add_work_note(incident_sys_id: str, note_text: str) -> None:
    """Add an internal-only work note for an escalated incident."""
    await _update_incident(incident_sys_id, {"work_notes": note_text})
