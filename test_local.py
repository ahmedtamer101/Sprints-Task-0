"""Run three local Gemini triage checks without HTTP or ServiceNow."""

import asyncio

from gemini_service import get_decision


TEST_CASES = [
    {
        "short_description": "Printer not printing after office move",
        "description": "It was working yesterday. I tried turning it off and on.",
        "expected": "respond",
    },
    {
        "short_description": "Cannot send email",
        "description": "It just doesn't work.",
        "expected": "ask",
    },
    {
        "short_description": "Request: annual leave approval",
        "description": "I would like to take next week off.",
        "expected": "escalate",
    },
]


async def main() -> None:
    for index, case in enumerate(TEST_CASES, start=1):
        result = await get_decision(
            case["short_description"],
            case["description"],
        )
        status = "PASS" if result["decision"] == case["expected"] else "FAIL"
        print(
            f"Case {index}: {status} "
            f"(expected={case['expected']}, actual={result['decision']})"
        )


if __name__ == "__main__":
    asyncio.run(main())
