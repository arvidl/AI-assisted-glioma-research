"""Teaching demonstrations for notebook 04: checks that can fail and a record validator.

The candidate solvers below are constructed for teaching. Two contain deliberate
bugs; they are not historical assistant outputs. The scenario functions are pure
and tested; the explorers only add widgets around them.
"""

import copy

import numpy as np

from glioma_ai.assistance import validate_record
from glioma_ai.neuroglial import integrate_potassium
from glioma_ai.notebook_display import show_figure

CHECK_NAMES = ("Analytic solution", "Balance", "Swap invariance")
SWAP_TOLERANCE_MM = 1e-12


def constant_input_exact(
    release_mM_per_s: float,
    astro_per_s: float,
    other_per_s: float,
    initial_mM: float,
    time_s: np.ndarray,
) -> np.ndarray:
    """Closed form k(t) = q/lambda + (k0 - q/lambda) exp(-lambda t); k0 + q t when lambda = 0."""
    rate = astro_per_s + other_per_s
    time = np.asarray(time_s, dtype=float)
    if rate == 0:
        return initial_mM + release_mM_per_s * time
    plateau = release_mM_per_s / rate
    return plateau + (initial_mM - plateau) * np.exp(-rate * time)


def _package(q, dt, astro, other, initial, steps):
    return integrate_potassium(np.full(steps, q), dt, astro, other, initial)


def _forward_euler(q, dt, astro, other, initial, steps):
    excess = np.empty(steps + 1)
    astro_cleared = np.zeros(steps + 1)
    other_cleared = np.zeros(steps + 1)
    excess[0] = initial
    for n in range(steps):
        excess[n + 1] = excess[n] + dt * (q - (astro + other) * excess[n])
        astro_cleared[n + 1] = astro_cleared[n] + dt * astro * excess[n]
        other_cleared[n + 1] = other_cleared[n] + dt * other * excess[n]
    return {
        "time_s": np.arange(steps + 1) * dt,
        "excess_mM": excess,
        "cumulative_release_mM": np.arange(steps + 1) * q * dt,
        "astro_cleared_mM": astro_cleared,
        "other_cleared_mM": other_cleared,
    }


def _omits_other_clearance(q, dt, astro, other, initial, steps):
    result = integrate_potassium(np.full(steps, q), dt, astro, 0.0, initial)
    result["other_cleared_mM"] = np.zeros(steps + 1)
    return result


def _left_endpoint_accounting(q, dt, astro, other, initial, steps):
    result = integrate_potassium(np.full(steps, q), dt, astro, other, initial)
    previous = result["excess_mM"][:-1]
    result["astro_cleared_mM"] = np.concatenate(([0.0], np.cumsum(dt * astro * previous)))
    result["other_cleared_mM"] = np.concatenate(([0.0], np.cumsum(dt * other * previous)))
    return result


CANDIDATES = {
    "Package (exact interval update)": _package,
    "Forward Euler": _forward_euler,
    "Bug: omits other clearance": _omits_other_clearance,
    "Bug: clearance booked from start of step": _left_endpoint_accounting,
}


def run_checks(
    dt_s: float = 0.05,
    astro_per_s: float = 0.8,
    other_per_s: float = 0.1,
    release_mM_per_s: float = 0.6,
    initial_mM: float = 0.2,
    duration_s: float = 10.0,
    tolerance_mM: float = 1e-9,
) -> dict:
    """Run every candidate through the three independent checks.

    Analytic: max |k - closed form| <= tolerance. Balance: max |initial + released
    - retained - cleared| <= tolerance. Swap invariance: exchanging the astrocytic
    and other rates changes the trace by at most SWAP_TOLERANCE_MM.
    """
    if dt_s <= 0 or duration_s <= 0 or tolerance_mM <= 0:
        raise ValueError("dt, duration and tolerance must be positive")
    steps = max(1, int(round(duration_s / dt_s)))
    args = (release_mM_per_s, dt_s)
    results = {}
    for name, solver in CANDIDATES.items():
        run = solver(*args, astro_per_s, other_per_s, initial_mM, steps)
        swapped = solver(*args, other_per_s, astro_per_s, initial_mM, steps)
        exact = constant_input_exact(
            release_mM_per_s, astro_per_s, other_per_s, initial_mM, run["time_s"]
        )
        residual = (
            initial_mM
            + run["cumulative_release_mM"]
            - run["excess_mM"]
            - run["astro_cleared_mM"]
            - run["other_cleared_mM"]
        )
        errors = {
            "Analytic solution": float(np.max(np.abs(run["excess_mM"] - exact))),
            "Balance": float(np.max(np.abs(residual))),
            "Swap invariance": float(np.max(np.abs(run["excess_mM"] - swapped["excess_mM"]))),
        }
        limits = {
            "Analytic solution": tolerance_mM,
            "Balance": tolerance_mM,
            "Swap invariance": SWAP_TOLERANCE_MM,
        }
        results[name] = {
            "run": run,
            "exact_mM": exact,
            "errors_mM": errors,
            "passed": {check: errors[check] <= limits[check] for check in CHECK_NAMES},
        }
    return {
        "candidates": results,
        "parameters": {
            "dt_s": dt_s,
            "astro_per_s": astro_per_s,
            "other_per_s": other_per_s,
            "release_mM_per_s": release_mM_per_s,
            "initial_mM": initial_mM,
            "duration_s": steps * dt_s,
            "tolerance_mM": tolerance_mM,
        },
    }


CANDIDATE_COLOURS = ("#1b7f8c", "#c46a3a", "#7a5aa6", "#8a8a8a")


def draw_check_state(figure, result):
    """Left: candidate traces against the closed form. Right: the pass/fail matrix."""
    figure.clear()
    trace_axis, matrix_axis = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.25, 1]})
    candidates = result["candidates"]
    first = next(iter(candidates.values()))
    trace_axis.plot(
        first["run"]["time_s"],
        first["exact_mM"],
        color="black",
        lw=3,
        alpha=0.25,
        label="Closed form",
    )
    for colour, (name, entry) in zip(CANDIDATE_COLOURS, candidates.items(), strict=True):
        trace_axis.plot(
            entry["run"]["time_s"], entry["run"]["excess_mM"], color=colour, lw=1.4, label=name
        )
    trace_axis.set(
        xlabel="Elapsed time (s)",
        ylabel="Excess extracellular K (mM)",
        title="Constant release; all candidates",
    )
    trace_axis.legend(fontsize=8, loc="best")
    names = list(candidates)
    matrix = np.array([[candidates[n]["passed"][c] for c in CHECK_NAMES] for n in names])
    matrix_axis.imshow(matrix, cmap="RdYlGn", vmin=-0.3, vmax=1.3, aspect="auto")
    for row, name in enumerate(names):
        for column, check in enumerate(CHECK_NAMES):
            error = candidates[name]["errors_mM"][check]
            verdict = "pass" if matrix[row, column] else "FAIL"
            matrix_axis.text(
                column, row, f"{verdict}\n{error:.1e} mM", ha="center", va="center", fontsize=8
            )
    matrix_axis.set_xticks(range(len(CHECK_NAMES)), CHECK_NAMES, fontsize=8)
    matrix_axis.set_yticks(range(len(names)), [n.replace(": ", ":\n") for n in names], fontsize=8)
    matrix_axis.set_title("Largest deviation and verdict")
    p = result["parameters"]
    figure.suptitle(
        f"Constructed check experiment: dt = {p['dt_s']:g} s, λa = {p['astro_per_s']:g}/s, "
        f"λo = {p['other_per_s']:g}/s, tolerance = {p['tolerance_mM']:.0e} mM"
    )
    figure.tight_layout()


def _panel(widgets, controls, show):
    return widgets.VBox([*controls.values(), widgets.interactive_output(show, controls)])


def check_explorer():
    """Sliders for dt, both clearance rates, release and the check tolerance."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    style = {"description_width": "11em"}
    layout = widgets.Layout(width="34em")

    def slider(cls, value, low, high, step, label, **extra):
        return cls(
            value=value,
            min=low,
            max=high,
            step=step,
            description=label,
            continuous_update=False,
            style=style,
            layout=layout,
            **extra,
        )

    controls = {
        "dt_s": slider(widgets.FloatLogSlider, 0.05, -3, 0.4, 0.1, "Step dt (s)", base=10),
        "astro_per_s": slider(widgets.FloatSlider, 0.8, 0, 2, 0.05, "λa astrocytic (1/s)"),
        "other_per_s": slider(widgets.FloatSlider, 0.1, 0, 2, 0.05, "λo other (1/s)"),
        "release_mM_per_s": slider(widgets.FloatSlider, 0.6, 0, 2, 0.05, "Release q (mM/s)"),
        "log_tolerance": slider(widgets.FloatSlider, -9, -14, -1, 1, "log10 tolerance (mM)"),
    }

    def show(dt_s, astro_per_s, other_per_s, release_mM_per_s, log_tolerance):
        figure = plt.figure(figsize=(13, 4.6))
        draw_check_state(
            figure,
            run_checks(
                dt_s, astro_per_s, other_per_s, release_mM_per_s, tolerance_mM=10.0**log_tolerance
            ),
        )
        show_figure(figure)

    return _panel(widgets, controls, show)


CONSTRUCTED_REVIEWER = "A. Reviewer (constructed example, not a real review)"


def record_variant(
    record: dict,
    decision: str | None = None,
    reviewer: str = "as recorded",
    checks: str = "as recorded",
    task: str = "as recorded",
    model: str = "as recorded",
) -> dict:
    """Copy of a record with one or more fields changed for a validator demonstration.

    reviewer: "as recorded", "none" or "constructed name"; checks: "as recorded",
    "empty list" or "placeholder"; task: "as recorded" or "blank"; model:
    "as recorded" or "blank". The original record is not modified.
    """
    variant = copy.deepcopy(record)
    if decision is not None:
        variant["decision"] = decision
    if reviewer == "none":
        variant["reviewer"] = None
    elif reviewer == "constructed name":
        variant["reviewer"] = CONSTRUCTED_REVIEWER
    if checks == "empty list":
        variant["checks"] = []
    elif checks == "placeholder":
        variant["checks"] = ["REPLACE"]
    if task == "blank":
        variant["task"] = " "
    if model == "blank":
        variant["model"] = ""
    return variant


def validation_outcome(record: dict) -> dict:
    """Return {'valid': bool, 'message': str} instead of raising."""
    try:
        validate_record(record)
    except ValueError as error:
        return {"valid": False, "message": str(error)}
    return {"valid": True, "message": "Structurally complete record."}


VALIDATOR_BLIND_SPOTS = (
    "whether the listed checks were actually run or passed",
    "whether the contribution and checks are scientifically adequate",
    "whether a named reviewer really reviewed the work",
    "whether the assistance improved speed, quality or patient benefit",
)


def validator_explorer(record: dict):
    """Dropdowns that alter a copy of a record and report the validator's verdict."""
    import ipywidgets as widgets
    from IPython.display import Markdown, display

    style = {"description_width": "9em"}
    layout = widgets.Layout(width="34em")

    def dropdown(options, value, label):
        return widgets.Dropdown(
            options=options, value=value, description=label, style=style, layout=layout
        )

    controls = {
        "decision": dropdown(
            ["pending_human_review", "accepted", "revised", "rejected"],
            record.get("decision", "pending_human_review"),
            "Decision",
        ),
        "reviewer": dropdown(
            ["as recorded", "none", "constructed name"], "as recorded", "Reviewer"
        ),
        "checks": dropdown(["as recorded", "empty list", "placeholder"], "as recorded", "Checks"),
        "task": dropdown(["as recorded", "blank"], "as recorded", "Task"),
        "model": dropdown(["as recorded", "blank"], "as recorded", "Model"),
    }

    def show(decision, reviewer, checks, task, model):
        variant = record_variant(record, decision, reviewer, checks, task, model)
        outcome = validation_outcome(variant)
        verdict = "**Accepted as complete.**" if outcome["valid"] else "**Refused.**"
        lines = [
            f"{verdict} {outcome['message']}",
            "",
            f"Decision `{variant['decision']}`, reviewer `{variant.get('reviewer')}`, "
            f"model `{variant.get('model')!s}`, {len(variant.get('checks') or [])} check(s).",
        ]
        if outcome["valid"]:
            lines += ["", "Even so, the validator cannot know:"]
            lines += [f"- {item}" for item in VALIDATOR_BLIND_SPOTS]
        display(Markdown("\n".join(lines)))

    return _panel(widgets, controls, show)
