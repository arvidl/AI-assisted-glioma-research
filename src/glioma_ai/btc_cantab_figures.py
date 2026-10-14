"""Figures and an explorer for notebook 10: group summaries and one named case.

Other participants appear only as group medians and quartiles, never as points.
"""

import numpy as np
from matplotlib.patches import FancyBboxPatch, Patch

from glioma_ai.btc_cantab import (
    GROUPS,
    INDICES,
    MEASURES,
    SESSIONS,
    case_change_table,
    case_scores,
    change_summary,
    group_summary,
    paired_values,
)
from glioma_ai.notebook_display import show_figure

GROUP_COLOURS = {"CON": "#7f7f7f", "MEN": "#31858f", "GLI": "#7b4f9d"}
CASE_COLOUR = "#c0392b"
SESSION_LABELS = {"preop": "Before surgery", "postop": "Follow-up"}


def _direction(code: str) -> str:
    return "higher is better" if MEASURES[code]["sense"] > 0 else "lower is better"


def draw_case(figure, cohort, case: str = "sub-PAT16"):
    """The case's six scores in native units against the controls' quartiles."""
    person = case_scores(cohort, case)
    figure.clear()
    axes = figure.subplots(2, 3).ravel()
    for axis, code in zip(axes, MEASURES, strict=True):
        spec = MEASURES[code]
        for x, session in enumerate(SESSIONS):
            rows = [
                r
                for r in group_summary(cohort, code)
                if r["group"] == "CON" and r["session"] == session
            ]
            if rows:
                row = rows[0]
                axis.fill_between([x - 0.18, x + 0.18], row["q1"], row["q3"], color="#dddddd", lw=0)
                axis.plot([x - 0.18, x + 0.18], [row["median"]] * 2, color="#7f7f7f", lw=1.5)
        before, after = person["scores"][code]
        axis.plot([0, 1], [before, after], "-o", color=CASE_COLOUR, lw=2, ms=7)
        for x, value, text in zip((0, 1), (before, after), person["text"][code], strict=True):
            axis.annotate(
                text if len(text) <= 7 else f"{value:.4g}",
                (x, value),
                xytext=(12, 0),
                textcoords="offset points",
                va="center",
                fontsize=9,
                color=CASE_COLOUR,
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.8},
            )
        axis.set(
            xticks=[0, 1],
            xticklabels=[SESSION_LABELS[s] for s in SESSIONS],
            xlim=(-0.5, 1.7),
            ylabel=spec["unit"],
            title=f"{spec['test']}: {spec['name']}\n({_direction(code)})",
        )
        axis.title.set_fontsize(9.5)
    figure.suptitle(
        f"{case}: released scores (red) and the controls' median and quartiles (grey), "
        "each measure in its own units",
        fontsize=11,
    )
    figure.tight_layout()


def draw_cohort(figure, cohort, case: str = "sub-PAT16"):
    """Median and quartiles per group and session, with the case overlaid."""
    person = case_scores(cohort, case)
    figure.clear()
    axes = figure.subplots(2, 3).ravel()
    offsets = {"CON": -0.25, "MEN": 0.0, "GLI": 0.25}
    for axis, code in zip(axes, MEASURES, strict=True):
        spec = MEASURES[code]
        summary = group_summary(cohort, code)
        for group in GROUPS:
            rows = [r for r in summary if r["group"] == group]
            xs = [SESSIONS.index(r["session"]) + offsets[group] for r in rows]
            medians = [r["median"] for r in rows]
            errors = [
                [r["median"] - r["q1"] for r in rows],
                [r["q3"] - r["median"] for r in rows],
            ]
            axis.errorbar(
                xs,
                medians,
                yerr=errors,
                fmt="s",
                color=GROUP_COLOURS[group],
                capsize=3,
                ms=6,
                label=f"{group}: {GROUPS[group]}",
            )
        before, after = person["scores"][code]
        axis.plot(
            [offsets["GLI"], 1 + offsets["GLI"]],
            [before, after],
            "-o",
            color=CASE_COLOUR,
            lw=1.5,
            ms=6,
            label=case,
        )
        axis.set(
            xticks=[0, 1],
            xticklabels=[SESSION_LABELS[s] for s in SESSIONS],
            xlim=(-0.6, 1.6),
            ylabel=spec["unit"],
            title=f"{spec['test']}: {spec['name']}\n({_direction(code)})",
        )
        axis.title.set_fontsize(9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=2, fontsize=9, frameon=False)
    figure.suptitle(
        "Group medians with quartile bars at each session (counts per measure in Table 2); "
        "fewer people were retested, so the two sessions are not the same groups",
        fontsize=11,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 1))


def draw_change_forest(figure, table: list[dict], case: str = "sub-PAT16"):
    """The case's indices, oriented so that right is better, with bootstrap intervals."""
    figure.clear()
    axis = figure.subplots()
    rows = [row for row in table if row["defined"]]
    markers = {"jacobson_truax": "o", "practice_adjusted": "s", "regression_based": "D"}
    shifts = {"jacobson_truax": -0.22, "practice_adjusted": 0.0, "regression_based": 0.22}
    axis.axvspan(-1.96, 1.96, color="#eeeeee", label="|index| ≤ 1.96")
    axis.axvline(0, color="black", lw=0.8)
    for y, row in enumerate(rows):
        for name, label in INDICES.items():
            sense = row["sense"]
            value = sense * row[name]
            low, high = sorted(sense * v for v in row["bootstrap"]["intervals"][name])
            axis.errorbar(
                value,
                y + shifts[name],
                xerr=[[value - low], [high - value]],
                fmt=markers[name],
                color=CASE_COLOUR if abs(value) > 1.96 else "#333333",
                capsize=2,
                ms=6,
                label=label if y == 0 else None,
            )
    axis.set(
        yticks=range(len(rows)),
        yticklabels=[f"{MEASURES[r['measure']]['short']}\n({r['measure']})" for r in rows],
        xlabel="Change index, oriented so that positive means better (worse ←  → better)",
        title=f"{case}: change indices against the retested controls (exploratory)",
    )
    axis.invert_yaxis()
    axis.legend(fontsize=8, loc="lower right")
    figure.tight_layout()


INFOGRAPHIC_COLOURS = {"preop": "#3d6fb0", "postop": "#c0504d"}
INFOGRAPHIC_SESSIONS = {"preop": "Pre-op", "postop": "Post-op (follow-up)"}
CHANGE_COLOURS = {1: "#3c8d3c", -1: "#c0504d", 0: "#9a9a9a"}
CHANGE_LABELS = {1: "Improved", -1: "Declined", 0: "Unchanged"}
INFOGRAPHIC_LABELS = {
    "MOT_latency_mean": ("MOT latency (ms)", "Motor screening"),
    "RTI_simpleRT_mean": ("RTI simple RT (ms)", "Processing speed"),
    "RTI_fiveRT": ("RTI five-choice RT (ms)", "Choice processing speed"),
    "RVP_A": ("RVP A′ (0 to 1)", "Sustained attention"),
    "SOC_prob_minmoves": ("SOC min-move problems (0 to 12)", "Spatial planning"),
    "SSP_spanlength": ("SSP span length (2 to 9)", "Visuospatial short-term memory"),
}
SOURCE_NOTE = (
    "Source: OpenNeuro ds001226 v5.0.1 (pre-op) and ds002080 v4.0.1 (post-op follow-up), CC0."
)


def _frame(figure, left, bottom, width, height, heading):
    figure.patches.append(
        FancyBboxPatch(
            (left, bottom),
            width,
            height,
            boxstyle="square,pad=0",
            transform=figure.transFigure,
            fill=False,
            ec="#555555",
            lw=1.2,
        )
    )
    figure.text(left, bottom + height + 0.008, heading, fontsize=15, va="bottom")


def _row_labels(axis, codes):
    axis.set_yticks(range(len(codes)))
    axis.set_yticklabels(
        [
            f"{INFOGRAPHIC_LABELS[c][0]}\n({INFOGRAPHIC_LABELS[c][1]}; {_direction(c)})"
            for c in codes
        ],
        fontsize=8.5,
    )
    axis.set_ylim(len(codes) - 0.45, -0.55)
    axis.tick_params(axis="y", length=0)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)


def _change_words(code: str, before: float, after: float, percent: float) -> str:
    if before == after:
        return "unchanged"
    if MEASURES[code]["unit"] == "ms":
        direction = "slower" if after > before else "faster"
    else:
        direction = "higher" if after > before else "lower"
    return f"{abs(percent):.1f}% {direction} ({'better' if percent > 0 else 'worse'})"


def draw_infographic(
    figure, cohort, table: list[dict], case: str = "sub-PAT16", source_note: str = SOURCE_NOTE
):
    """The pre/post slide's layout redrawn from the released scores.

    Bar length is the score as a fraction of the measure's axis: the full scale where the
    measure is bounded, and one common millisecond axis for the timed measures. Every
    printed number and every conclusion is computed from the cohort and the change table.
    """
    person = case_scores(cohort, case)
    summary = {row["measure"]: row for row in change_summary(table)}
    codes = [code for code in MEASURES if code in summary]
    timed = [v for c in codes if MEASURES[c]["unit"] == "ms" for v in person["scores"][c]]
    time_axis = 250 * np.ceil(max(timed) / 250) if timed else None
    figure.clear()
    figure.text(
        0.5,
        0.965,
        f"CANTAB Cognitive Assessment: {case} Pre-op vs Post-op",
        ha="center",
        va="top",
        fontsize=20,
    )
    figure.text(
        0.5,
        0.915,
        "Reconstructed from the released scores; every number below is computed in notebook 10",
        ha="center",
        va="top",
        fontsize=10.5,
        color="#444444",
    )

    _frame(figure, 0.02, 0.385, 0.47, 0.46, "Raw scores")
    raw = figure.add_axes((0.215, 0.46, 0.26, 0.34))
    for i, code in enumerate(codes):
        values = person["scores"][code]
        high = MEASURES[code]["bounds"][1] or time_axis
        for shift, session, value in zip((-0.19, 0.19), SESSIONS, values, strict=True):
            raw.barh(i + shift, value / high, height=0.36, color=INFOGRAPHIC_COLOURS[session])
            raw.text(value / high + 0.015, i + shift, f"{value:.4g}", va="center", fontsize=8.5)
    _row_labels(raw, codes)
    raw.set_xlim(0, 1.18)
    raw.set_xticks([0, 0.5, 1])
    raw.set_xticklabels(["0", "½", "axis max"], fontsize=8)
    raw.set_xlabel(
        f"Bar length = score ÷ axis maximum (timed tests 0–{time_axis:.0f} ms; others full scale)",
        fontsize=8,
    )
    raw.legend(
        handles=[
            Patch(color=INFOGRAPHIC_COLOURS[s], label=INFOGRAPHIC_SESSIONS[s]) for s in SESSIONS
        ],
        fontsize=8,
        loc="lower right",
        bbox_to_anchor=(1.04, 1.0),
        ncol=3,
        frameon=False,
    )

    _frame(figure, 0.51, 0.385, 0.47, 0.46, "Normalised change (pre → post)")
    change = figure.add_axes((0.705, 0.46, 0.26, 0.34))
    percents = [summary[code]["percent"] for code in codes]
    reach = max(max(abs(p) for p in percents), 5) * 1.75
    for i, (code, percent) in enumerate(zip(codes, percents, strict=True)):
        row = summary[code]
        sign = int(np.sign(round(percent, 1)))
        change.barh(i, percent, height=0.55, color=CHANGE_COLOURS[sign])
        index = row["oriented"][row["largest"]]
        change.text(
            percent + (0.03 if percent >= 0 else -0.03) * reach,
            i,
            f"{percent:+.1f}%\nindex {index:+.2f}" if sign else f"0%\nindex {index:+.2f}",
            ha="left" if percent >= 0 else "right",
            va="center",
            fontsize=8,
        )
    _row_labels(change, codes)
    change.axvline(0, color="black", lw=0.8)
    change.set_xlim(-reach, reach)
    change.tick_params(axis="x", labelsize=8)
    change.set_xlabel("% change from pre-op, signed so that positive = better", fontsize=8)
    change.legend(
        handles=[Patch(color=CHANGE_COLOURS[s], label=CHANGE_LABELS[s]) for s in (1, -1, 0)],
        fontsize=8,
        loc="lower right",
        bbox_to_anchor=(1.04, 1.0),
        ncol=3,
        frameon=False,
    )

    _frame(figure, 0.02, 0.025, 0.96, 0.29, "Conclusions (computed from the change indices)")
    lines = []
    for code in codes:
        row = summary[code]
        before, after = person["scores"][code]
        index = row["oriented"][row["largest"]]
        verdict = row["verdict"].replace(" on all three indices", "")
        lines.append(
            (
                f"{MEASURES[code]['short']}:",
                f"{before:.4g} → {after:.4g} {MEASURES[code]['unit']}, "
                f"{_change_words(code, before, after, row['percent'])}; largest index "
                f"{index:+.2f} ({INDICES[row['largest']].lower()}): {verdict}",
            )
        )
    n = next(iter(summary.values()))["n_reference"]
    reliable = [MEASURES[c]["short"] for c in codes if summary[c]["verdict"].startswith("reliable")]
    closest = max(codes, key=lambda c: abs(summary[c]["oriented"][summary[c]["largest"]]))
    top = summary[closest]
    lines.append(
        (
            "Overall:",
            (
                f"Reliable change in {', '.join(reliable)}"
                if reliable
                else "No measure changed reliably (all three indices within ±1.96)"
            )
            + f" against {n} retested controls.\nClosest: {MEASURES[closest]['short']}, "
            f"{INDICES[top['largest']].lower()} {top['oriented'][top['largest']]:+.2f}, beyond "
            f"±1.96 in {100 * top['share_beyond']:.0f}% of bootstrap resamples",
        )
    )
    for k, (heading, text) in enumerate(lines):
        y = 0.29 - k * 0.029
        figure.text(0.035, y, heading, fontsize=9.5, weight="bold", va="top")
        figure.text(0.215, y, text, fontsize=9.5, va="top")
    figure.text(
        0.035,
        0.045,
        "Exploratory single case. Percentages and indices are signed so that positive is better; "
        "a change is called reliable only when the Jacobson–Truax, practice-adjusted and "
        "regression-based indices all exceed ±1.96.\nValues rounded to four significant digits. "
        + source_note,
        fontsize=7.5,
        color="#444444",
        va="bottom",
    )


def most_extreme_control(cohort, code: str) -> str:
    """ID of the control with the largest absolute retest change (used internally only)."""
    controls = [
        p
        for p in cohort
        if p["group"] == "CON"
        and p["scores"]["postop"] is not None
        and p["scores"]["preop"][code] is not None
        and p["scores"]["postop"][code] is not None
    ]
    return max(
        controls, key=lambda p: abs(p["scores"]["postop"][code] - p["scores"]["preop"][code])
    )["id"]


def change_scenario(cohort, code: str, leave_out_extreme: bool = False, n_boot: int = 2000):
    exclude = (most_extreme_control(cohort, code),) if leave_out_extreme else ()
    table = case_change_table(cohort, exclude=exclude, n_boot=n_boot)
    row = next(r for r in table if r["measure"] == code)
    x, y = paired_values(cohort, code, "CON", exclude=exclude)
    return {"row": row, "control_changes": y - x, "leave_out_extreme": leave_out_extreme}


def draw_change_scenario(figure, run, case: str = "sub-PAT16"):
    row = run["row"]
    code, stats = row["measure"], row["reference"]
    spec = MEASURES[code]
    figure.clear()
    left, right = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.2, 1]})
    q1, median, q3 = np.percentile(run["control_changes"], [25, 50, 75])
    band = 1.96 * np.sqrt(2) * stats["sd_baseline"] * np.sqrt(1 - stats["r"])
    left.axvspan(
        stats["practice"] - band,
        stats["practice"] + band,
        color="#eeeeee",
        label="practice ± 1.96·S_diff",
    )
    left.errorbar(
        median,
        0.35,
        xerr=[[median - q1], [q3 - median]],
        fmt="s",
        color=GROUP_COLOURS["CON"],
        capsize=3,
        label=f"Controls' change: median and quartiles (n {stats['n']})",
    )
    change = row["follow_up"] - row["baseline"]
    left.plot([change], [0.65], "o", color=CASE_COLOUR, ms=10, label=f"{case}: {change:+.3g}")
    left.axvline(0, color="black", lw=0.8)
    reach = max(abs(change), abs(stats["practice"]) + band, abs(q1), abs(q3)) * 1.15
    left.set_xlim(-reach, reach)
    left.set(
        ylim=(0, 1),
        yticks=[],
        xlabel=f"Follow-up − baseline ({spec['unit']}; {_direction(code)})",
        title=f"{spec['short']}: change in native units",
    )
    left.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2)
    names = list(INDICES)
    values = [row["sense"] * row[n] for n in names]
    intervals = [sorted(row["sense"] * v for v in row["bootstrap"]["intervals"][n]) for n in names]
    right.axvspan(-1.96, 1.96, color="#eeeeee")
    right.axvline(0, color="black", lw=0.8)
    for y, (value, (low, high)) in enumerate(zip(values, intervals, strict=True)):
        right.errorbar(
            value, y, xerr=[[value - low], [high - value]], fmt="o", color="#333333", capsize=3
        )
    right.set(
        yticks=range(len(names)),
        yticklabels=[INDICES[n] for n in names],
        xlabel="Index (positive = better)",
        title="Indices with 95% bootstrap intervals",
    )
    right.invert_yaxis()
    note = "; most extreme control left out" if run["leave_out_extreme"] else ""
    figure.suptitle(
        f"Exploratory: reference = retested controls (partners/caregivers), r = {stats['r']:.2f}, "
        f"practice {stats['practice']:+.3g} {spec['unit']}{note}",
        fontsize=10.5,
    )
    figure.tight_layout()


def change_explorer(cohort):
    """Measure and robustness controls for the case's reliable-change indices."""
    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    style = {"description_width": "16em"}
    layout = widgets.Layout(width="36em")
    controls = {
        "code": widgets.Dropdown(
            options=list(MEASURES),
            value="SSP_spanlength",
            description="Measure",
            style=style,
            layout=layout,
        ),
        "leave_out_extreme": widgets.Checkbox(
            value=False,
            description="Leave out the control with the largest change",
            style=style,
            layout=layout,
        ),
    }

    def show(code, leave_out_extreme):
        figure = plt.figure(figsize=(13, 4))
        draw_change_scenario(figure, change_scenario(cohort, code, leave_out_extreme))
        show_figure(figure)

    return widgets.VBox([*controls.values(), widgets.interactive_output(show, controls)])
