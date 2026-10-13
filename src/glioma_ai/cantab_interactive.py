"""Interactive teaching views for notebook 10: score precision and reliable change.

All inputs entered here are hypothetical. The pinned release supplies no retest
reliability or reference SD, so no patient change is classified by this module.
"""

import numpy as np

from glioma_ai.cantab import METRICS, precision_agreement, precision_interval, reliable_change_index
from glioma_ai.notebook_display import show_figure


def measure_table() -> list[dict]:
    """Name, unit and direction of each released measure, from METRICS."""
    return [
        {
            "code": code,
            "name": spec["name"],
            "unit": spec["unit"],
            "direction": "higher is better" if spec["sense"] > 0 else "lower is better",
        }
        for code, spec in METRICS.items()
    ]


def precision_scenario(source: str = "0.70", local: str = "0.702") -> dict:
    return {
        "source": source,
        "local": local,
        "verdict": precision_agreement(source, local),
        "interval": precision_interval(source),
    }


def draw_precision_state(axis, run):
    interval = run["interval"]
    source, local = float(run["source"]), float(run["local"])
    span = max(3 * interval["quantum"], abs(local - source) * 1.6)
    axis.axvspan(
        interval["low"], interval["high"], color="#cfe8d5", label="Rounds to the released score"
    )
    axis.axvline(source, color="black", lw=1.5, label=f"Released {run['source']}")
    colour = {"exact": "#2a7f3f", "at_release_precision": "#2a7f3f"}.get(run["verdict"], "#c0392b")
    axis.plot([local], [0.5], "o", color=colour, ms=10, label=f"Local {run['local']}")
    axis.set(
        xlim=(source - span, source + span),
        ylim=(0, 1),
        yticks=[],
        xlabel="Score (released units)",
        title=f"Verdict: {run['verdict']}  (last released digit = {interval['quantum']:g})",
    )
    axis.legend(fontsize=8, loc="upper right")


def precision_explorer():
    """Text boxes for a released score and a local value with more or fewer digits."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    style = {"description_width": "12em"}
    controls = {
        "source": widgets.Text(
            value="0.70", description="Released score", style=style, continuous_update=False
        ),
        "local": widgets.Text(
            value="0.702", description="Local value", style=style, continuous_update=False
        ),
    }

    def show(source, local):
        try:
            run = precision_scenario(source, local)
        except ValueError as error:
            print("Not a valid decimal score:", error)
            return
        figure, axis = plt.subplots(figsize=(10, 2.4))
        draw_precision_state(axis, run)
        figure.tight_layout()
        show_figure(figure)

    return widgets.VBox([*controls.values(), widgets.interactive_output(show, controls)])


def change_scenario(
    measure: str = "SSP_spanlength",
    baseline: float = 5.0,
    follow_up: float = 6.0,
    baseline_sd: float = 1.2,
    reliability: float = 0.6,
) -> dict:
    """Reliable change for hypothetical inputs, with the measure's unit and direction."""
    spec = METRICS[measure]
    result = reliable_change_index(baseline, follow_up, baseline_sd, reliability)
    change = follow_up - baseline
    if not result["reliable"]:
        reading = "within measurement error"
    elif change * spec["sense"] > 0:
        reading = "reliable improvement"
    else:
        reading = "reliable decline"
    reliabilities = np.linspace(0, 0.95, 96)
    return {
        **result,
        "change": change,
        "reading": reading,
        "measure": measure,
        "name": spec["name"],
        "unit": spec["unit"],
        "reliabilities": reliabilities,
        "minimum_curve": 1.96 * np.sqrt(2) * baseline_sd * np.sqrt(1 - reliabilities),
        "parameters": {
            "baseline": baseline,
            "follow_up": follow_up,
            "baseline_sd": baseline_sd,
            "reliability": reliability,
        },
    }


def draw_change_state(figure, run):
    figure.clear()
    line, curve = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.3, 1]})
    threshold, change = run["minimum_reliable_change"], run["change"]
    span = max(1.6 * threshold, 1.3 * abs(change), 1e-9)
    line.axvspan(
        -threshold,
        threshold,
        color="#e6e6e6",
        label=f"|change| ≤ 1.96·S_diff = {threshold:.2f} {run['unit']}",
    )
    line.axvline(0, color="black", lw=0.8)
    colour = {"reliable improvement": "#2a7f3f", "reliable decline": "#c0392b"}.get(
        run["reading"], "#555555"
    )
    line.plot(
        [change],
        [0.5],
        "o",
        color=colour,
        ms=11,
        label=f"Observed change {change:+.2f} {run['unit']}",
    )
    line.set(
        xlim=(-span, span),
        ylim=(0, 1),
        yticks=[],
        xlabel=f"Follow-up − baseline ({run['unit']})",
        title=f"RCI = {run['rci']:+.2f}: {run['reading']}",
    )
    line.legend(fontsize=8, loc="upper left")
    curve.plot(run["reliabilities"], run["minimum_curve"], color="#31858f")
    p = run["parameters"]
    curve.plot([p["reliability"]], [threshold], "o", color="black")
    curve.set(
        xlabel="Test–retest reliability r",
        ylabel=f"Smallest reliable change ({run['unit']})",
        title=f"At SD = {p['baseline_sd']:g} {run['unit']}",
    )
    direction = "higher is better" if METRICS[run["measure"]]["sense"] > 0 else "lower is better"
    figure.suptitle(
        f"HYPOTHETICAL inputs, {run['name']} ({run['measure']}, {direction}): baseline "
        f"{p['baseline']:g}, follow-up {p['follow_up']:g}, SD {p['baseline_sd']:g}, r = "
        f"{p['reliability']:g}"
    )
    figure.tight_layout()


HYPOTHETICAL_PRESETS = {
    "MOT_latency_mean": {
        "baseline": 700,
        "follow_up": 650,
        "sd": 150,
        "score": (200, 2000, 10),
        "sd_range": (10, 500, 10),
    },
    "RTI_fiveRT": {
        "baseline": 350,
        "follow_up": 330,
        "sd": 60,
        "score": (150, 1000, 5),
        "sd_range": (5, 200, 5),
    },
    "RVP_A": {
        "baseline": 0.90,
        "follow_up": 0.92,
        "sd": 0.04,
        "score": (0.5, 1.0, 0.005),
        "sd_range": (0.005, 0.2, 0.005),
    },
    "SOC_prob_minmoves": {
        "baseline": 8,
        "follow_up": 9,
        "sd": 2,
        "score": (0, 12, 1),
        "sd_range": (0.2, 5, 0.1),
    },
    "SSP_spanlength": {
        "baseline": 5,
        "follow_up": 6,
        "sd": 1.2,
        "score": (2, 9, 1),
        "sd_range": (0.1, 3, 0.1),
    },
}


def change_explorer():
    """Measure dropdown and sliders for hypothetical scores, SD and reliability.

    Choosing a measure loads illustrative hypothetical values and slider ranges in that
    measure's units; they are not norms or released statistics.
    """
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    style = {"description_width": "14em"}
    layout = widgets.Layout(width="34em")

    def slider(label):
        return widgets.FloatSlider(
            description=label,
            continuous_update=False,
            style=style,
            layout=layout,
            readout_format=".3g",
        )

    controls = {
        "measure": widgets.Dropdown(
            options=list(METRICS),
            value="SSP_spanlength",
            description="Measure",
            style=style,
            layout=layout,
        ),
        "baseline": slider("Baseline score (hypothetical)"),
        "follow_up": slider("Follow-up score (hypothetical)"),
        "baseline_sd": slider("Reference SD (hypothetical)"),
        "reliability": widgets.FloatSlider(
            value=0.6,
            min=0.0,
            max=0.95,
            step=0.05,
            description="Retest reliability r (hypothetical)",
            continuous_update=False,
            style=style,
            layout=layout,
        ),
    }

    def load(measure):
        preset = HYPOTHETICAL_PRESETS[measure]
        for name, value, (low, high, step) in (
            ("baseline", preset["baseline"], preset["score"]),
            ("follow_up", preset["follow_up"], preset["score"]),
            ("baseline_sd", preset["sd"], preset["sd_range"]),
        ):
            control = controls[name]
            control.min, control.max = -1e9, 1e9
            control.step, control.value = step, value
            control.min, control.max = low, high

    load("SSP_spanlength")
    controls["measure"].observe(lambda change: load(change["new"]), names="value")

    def show(**values):
        figure = plt.figure(figsize=(13, 4))
        draw_change_state(figure, change_scenario(**values))
        show_figure(figure)

    return widgets.VBox([*controls.values(), widgets.interactive_output(show, controls)])
