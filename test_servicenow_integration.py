"""Unit tests for ServiceNow write-back and decision routing."""

import asyncio
import unittest
from unittest.mock import patch

import main
import servicenow_service
from models import IncidentPayload


class _Response:
    def raise_for_status(self) -> None:
        pass


class _Client:
    instances: list["_Client"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.request: tuple[str, dict] | None = None
        self.__class__.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        pass

    async def patch(self, url: str, json: dict) -> _Response:
        self.request = (url, json)
        return _Response()


class ServiceNowWriteBackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        _Client.instances.clear()
        self.client_patch = patch.object(
            servicenow_service.httpx, "AsyncClient", _Client
        )
        self.client_patch.start()

    async def asyncTearDown(self) -> None:
        self.client_patch.stop()

    async def test_resolve_incident_sets_expected_fields(self) -> None:
        await servicenow_service.resolve_incident("abc123", "Restart the print spooler.")

        client = _Client.instances[0]
        self.assertEqual(
            client.request,
            (
                f"{servicenow_service.SN_INSTANCE_URL.rstrip('/')}/api/now/table/incident/abc123",
                {
                    "work_notes": "Restart the print spooler.",
                    "close_notes": "Restart the print spooler.",
                    "state": 6,
                    "close_code": "Solution provided",
                },
            ),
        )
        self.assertEqual(client.kwargs["headers"], {"Content-Type": "application/json"})

    async def test_comment_and_work_note_use_the_correct_fields(self) -> None:
        await servicenow_service.add_customer_comment("ask-id", "Which error appears?")
        await servicenow_service.add_work_note("escalate-id", "Sent to desktop support.")

        self.assertEqual(_Client.instances[0].request[1], {"comments": "Which error appears?"})
        self.assertEqual(
            _Client.instances[1].request[1],
            {"work_notes": "Sent to desktop support."},
        )

    async def test_write_back_failure_is_logged_and_not_raised(self) -> None:
        class FailingClient(_Client):
            async def patch(self, url: str, json: dict) -> _Response:
                raise RuntimeError("ServiceNow unavailable")

        with patch.object(servicenow_service.httpx, "AsyncClient", FailingClient):
            with self.assertLogs(servicenow_service.logger, level="ERROR") as logs:
                await servicenow_service.add_work_note("failure-id", "Escalated")

        self.assertIn("ServiceNow write-back failed for incident failure-id", logs.output[0])


class TriageRoutingTests(unittest.TestCase):
    def test_each_gemini_decision_routes_message_to_the_matching_write_back(self) -> None:
        payload = IncidentPayload(
            incident_sys_id="incident-id",
            number="INC0010001",
            short_description="Example",
            priority=3,
        )

        for decision, expected_function in (
            ("respond", "resolve"),
            ("ask", "comment"),
            ("escalate", "note"),
        ):
            calls: list[tuple[str, str, str]] = []

            async def get_decision(short_description: str, description: str) -> dict:
                return {"decision": decision, "message": "Gemini message"}

            async def record(function: str, incident_id: str, message: str) -> None:
                calls.append((function, incident_id, message))

            async def resolve(incident_id: str, message: str) -> None:
                await record("resolve", incident_id, message)

            async def comment(incident_id: str, message: str) -> None:
                await record("comment", incident_id, message)

            async def note(incident_id: str, message: str) -> None:
                await record("note", incident_id, message)

            with (
                patch.object(main, "get_decision", get_decision),
                patch.object(main, "resolve_incident", resolve),
                patch.object(main, "add_customer_comment", comment),
                patch.object(main, "add_work_note", note),
            ):
                asyncio.run(main.triage_incident(payload))

            self.assertEqual(calls, [(expected_function, "incident-id", "Gemini message")])
