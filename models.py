"""Pydantic models for incoming webhook payloads."""

from pydantic import BaseModel


class IncidentPayload(BaseModel):
    incident_sys_id: str
    number: str
    short_description: str
    description: str = ""
    priority: int
