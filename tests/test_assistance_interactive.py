import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from glioma_ai.assistance_interactive import (
    CHECK_NAMES,
    CONSTRUCTED_REVIEWER,
    draw_check_state,
    record_variant,
    run_checks,
    validation_outcome,
)

RECORD = json.loads(
    (
        Path(__file__).resolve().parents[1] / "docs/ai-records/2026-10-06-neuroglial-cognition.json"
    ).read_text()
)


def verdicts(result):
    return {
        name: tuple(entry["passed"][check] for check in CHECK_NAMES)
        for name, entry in result["candidates"].items()
    }


def test_each_check_catches_a_different_flaw():
    found = verdicts(run_checks())
    assert found["Package (exact interval update)"] == (True, True, True)
    assert found["Forward Euler"] == (False, True, True)
    assert found["Bug: omits other clearance"] == (False, True, False)
    assert found["Bug: clearance booked from start of step"] == (True, False, True)


def test_bug_is_invisible_when_parameters_do_not_exercise_it():
    found = verdicts(run_checks(other_per_s=0.0))
    assert found["Bug: omits other clearance"][0]
    found = verdicts(run_checks(astro_per_s=0.4, other_per_s=0.4))
    assert found["Bug: omits other clearance"][2]


def test_forward_euler_is_first_order_and_tolerance_decides():
    coarse = run_checks(dt_s=0.02)["candidates"]["Forward Euler"]["errors_mM"]
    fine = run_checks(dt_s=0.01)["candidates"]["Forward Euler"]["errors_mM"]
    assert coarse["Analytic solution"] / fine["Analytic solution"] == pytest.approx(2, rel=0.05)
    loose = run_checks(dt_s=0.01, tolerance_mM=1e-2)["candidates"]["Forward Euler"]
    assert loose["passed"]["Analytic solution"]


def test_zero_clearance_closed_form():
    entry = run_checks(astro_per_s=0, other_per_s=0)["candidates"]
    assert all(entry["Package (exact interval update)"]["passed"].values())


def test_validator_variants():
    assert validation_outcome(RECORD)["valid"]
    unsigned = record_variant(RECORD, decision="accepted", reviewer="none")
    assert "named reviewer" in validation_outcome(unsigned)["message"]
    signed = record_variant(RECORD, decision="accepted", reviewer="constructed name")
    assert validation_outcome(signed)["valid"] and signed["reviewer"] == CONSTRUCTED_REVIEWER
    assert not validation_outcome(record_variant(RECORD, checks="placeholder"))["valid"]
    assert not validation_outcome(record_variant(RECORD, checks="empty list"))["valid"]
    assert not validation_outcome(record_variant(RECORD, task="blank"))["valid"]
    assert not validation_outcome(record_variant(RECORD, model="blank"))["valid"]
    assert RECORD["decision"] == "pending_human_review" and RECORD["reviewer"] is None


def test_check_figure_renders():
    figure = plt.figure()
    draw_check_state(figure, run_checks())
    assert len(figure.axes) == 2
    plt.close(figure)
