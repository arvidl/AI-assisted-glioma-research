"""Check documentation completeness without fabricating review or AI benefit."""

from datetime import date


def validate_record(record: dict) -> dict:
    """Return a valid record, or fail when required evidence is missing.

    A structurally valid record is not evidence that its content is true.
    Human-review decisions must name a reviewer; pending review need not.
    """
    if record.get("schema") != "glioma-ai-assistance-v1":
        raise ValueError("Unknown assistance schema.")
    for field in (
        "task",
        "tool",
        "model",
        "input_classification",
        "instruction_summary",
        "contribution",
        "artifact_reference",
    ):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip() or value == "REPLACE":
            raise ValueError(f"Record needs a completed {field}.")
    try:
        date.fromisoformat(record["date"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Record date must be an ISO calendar date.") from error
    if record.get("record_type") not in {"retrospective_summary", "prospective_interaction"}:
        raise ValueError("Specify how the interaction was recorded.")
    checks = record.get("checks")
    if (
        not isinstance(checks, list)
        or not checks
        or any(
            not isinstance(check, str) or not check.strip() or check == "REPLACE"
            for check in checks
        )
    ):
        raise ValueError("Supply at least one concrete check.")
    decision = record.get("decision")
    if decision not in {"pending_human_review", "accepted", "revised", "rejected"}:
        raise ValueError("Unknown decision status.")
    reviewer = record.get("reviewer")
    if decision != "pending_human_review" and (
        not isinstance(reviewer, str) or not reviewer.strip()
    ):
        raise ValueError("A human decision requires a named reviewer.")
    questions = record.get("unresolved_questions")
    if not isinstance(questions, list) or any(not isinstance(q, str) for q in questions):
        raise ValueError("Unresolved questions must be a list of strings.")
    return record
