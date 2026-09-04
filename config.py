"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv


load_dotenv()

_REQUIRED_ENV_VARS = (
    "GEMINI_API_KEY",
    "SN_INSTANCE_URL",
    "SN_USERNAME",
    "SN_PASSWORD",
)

_missing_vars = [name for name in _REQUIRED_ENV_VARS if not os.getenv(name)]
if _missing_vars:
    raise RuntimeError(
        "Missing required environment variable(s): " + ", ".join(_missing_vars)
    )

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SN_INSTANCE_URL = os.environ["SN_INSTANCE_URL"]
SN_USERNAME = os.environ["SN_USERNAME"]
SN_PASSWORD = os.environ["SN_PASSWORD"]
