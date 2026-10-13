"""Generate the synthetic niche and cancer-neuroscience teaching evidence."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from glioma_ai.biology import NeuronGliomaParameters, niche_transition, simulate_neuron_glioma


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _save(figure, output: Path, name: str) -> None:
    figure.savefig(output / f"{name}.png", dpi=180, bbox_inches="tight")
    figure.savefig(output / f"{name}.pdf", bbox_inches="tight")
    plt.close(figure)


def niche_example(output: Path) -> dict:
    """One fixed cue changes state composition while local total is conserved."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    coordinates = np.arange(61, dtype=float) - 30
    x, y = np.meshgrid(coordinates, coordinates, indexing="ij")
    total = 0.7 * np.exp(-(x**2 + y**2) / (2 * 9**2))
    signal = np.exp(-((x - 7) ** 2 + y**2) / (2 * 8**2))
    other, mes = 0.9 * total, 0.1 * total
    times = np.linspace(0, 10, 51)
    fraction, no_cue_fraction = [], []
    for day in times:
        _, q = niche_transition(other, mes, signal, 0.08, 0.02, day)
        _, q0 = niche_transition(other, mes, np.zeros_like(signal), 0.08, 0.02, day)
        fraction.append(float(q.sum() / total.sum()))
        no_cue_fraction.append(float(q0.sum() / total.sum()))
    final_other, final_mes = niche_transition(other, mes, signal, 0.08, 0.02, 10)
    summary = {
        "evidence_type": "synthetic",
        "state_meanings": {
            "other": "aggregate analogue of other tumor states",
            "mes_like": "MES-like program analogue, not an assayed phenotype",
            "signal": "fixed normalized macrophage-associated cue, not a measured immune count",
        },
        "coordinate_space": "constructed 61 by 61 plane; 1 mm grid, not patient space",
        "equation": "dM/dt = k_forward*s*P - k_reverse*M; dP/dt = -dM/dt",
        "solver": "exact fixed-cue two-state transition",
        "parameters": {"forward_per_day": 0.08, "reverse_per_day": 0.02, "elapsed_days": 10},
        "initial_mes_like_fraction": 0.1,
        "final_mes_like_fraction": fraction[-1],
        "no_cue_final_mes_like_fraction": no_cue_fraction[-1],
        "total_density_change_max_abs": float(np.max(np.abs(final_other + final_mes - total))),
        "omitted": ["growth", "migration", "death", "immune-cell dynamics", "MRI forward model"],
        "inferred_cell_state": False,
        "human_rate_calibration": "not_performed",
        "biological_motivation_doi": "10.1016/j.ccell.2021.05.002",
    }
    figure, axes = plt.subplots(1, 4, figsize=(13.2, 3.7), constrained_layout=True)
    for axis, field, title, maximum in zip(
        axes[:3],
        (total, signal, final_mes / total),
        ("Unchanged total density", "Prescribed niche cue", "Final MES-like fraction"),
        (1, 1, 1),
        strict=True,
    ):
        im = axis.imshow(
            field.T,
            origin="lower",
            extent=(-30.5, 30.5, -30.5, 30.5),
            vmin=0,
            vmax=maximum,
            cmap="viridis",
        )
        axis.set_title(title, fontsize=10)
        axis.set_xlabel("Constructed x (mm)")
        axis.set_ylabel("Constructed y (mm)")
        figure.colorbar(im, ax=axis, shrink=0.7).set_label("Dimensionless")
    axes[3].plot(times, fraction, color="#31858f", label="Prescribed cue")
    axes[3].plot(times, no_cue_fraction, color="#555555", label="No cue")
    axes[3].set(
        xlabel="Prescribed elapsed time (days)",
        ylabel="Overall MES-like fraction",
        ylim=(0, 0.5),
        title="Composition changes",
    )
    axes[3].legend(fontsize=8)
    figure.suptitle(
        "Synthetic niche experiment: state composition can change at fixed total density"
    )
    _save(figure, output, "microenvironment")
    np.savez_compressed(
        output / "synthetic_niche.npz",
        total=total,
        signal=signal,
        other=final_other,
        mes_like=final_mes,
    )
    _talk_views(output, total, final_mes / total, None)
    _write(output / "microenvironment.json", summary)
    return summary


def neuron_glioma_construction() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return grid coordinates, density, and prescribed slow signal drive."""
    coordinates = np.arange(61, dtype=float) - 30
    x, y = np.meshgrid(coordinates, coordinates, indexing="ij")
    initial = 0.35 * np.exp(-((x + 5) ** 2 + y**2) / (2 * 4**2))
    drive = 0.1 + 0.7 * np.exp(-((x - 4) ** 2 + (y - 2) ** 2) / (2 * 7**2))
    return coordinates, initial, drive


def _talk_views(output: Path, total, mes_fraction, trajectories) -> None:
    """Generate large-label views of the same arrays for a projected slide."""
    with plt.rc_context(
        {
            "font.size": 15,
            "axes.titlesize": 16,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 12,
        }
    ):
        if total is not None:
            figure, axes = plt.subplots(1, 2, figsize=(9, 3.5), constrained_layout=True)
            for axis, field, title in zip(
                axes,
                (total, mes_fraction),
                ("Fixed total density", "MES-like fraction after 10 days"),
                strict=True,
            ):
                im = axis.imshow(
                    field.T,
                    origin="lower",
                    extent=(-30.5, 30.5, -30.5, 30.5),
                    vmin=0,
                    vmax=1,
                    cmap="viridis",
                )
                axis.set(xlabel="Constructed x (mm)", ylabel="Constructed y (mm)", title=title)
                figure.colorbar(im, ax=axis, shrink=0.75).set_label("Dimensionless")
            _save(figure, output, "microenvironment_talk")
        if trajectories is None:
            return
        figure, axes = plt.subplots(1, 3, figsize=(11.5, 3.6), constrained_layout=True)
        for axis, key, title in zip(
            axes[:2], ("baseline", "feedback"), ("Baseline density", "Coupled density"), strict=True
        ):
            im = axis.imshow(
                trajectories[key]["density"].T,
                origin="lower",
                extent=(-30.5, 30.5, -30.5, 30.5),
                vmin=0,
                vmax=1,
                cmap="magma",
            )
            axis.set(
                xlabel="Constructed x (mm)",
                ylabel="Constructed y (mm)",
                title=title,
                xlim=(-20, 20),
                ylim=(-20, 20),
            )
            figure.colorbar(im, ax=axis, shrink=0.75)
        for key, label, color in zip(
            trajectories,
            ("Baseline", "One-way", "Feedback"),
            ("#555555", "#31858f", "#d67645"),
            strict=True,
        ):
            axes[2].plot(
                trajectories[key]["time_days"],
                trajectories[key]["density_integral_mm2"],
                color=color,
                label=label,
            )
        axes[2].set(
            xlabel="Elapsed time (days)",
            ylabel="Density integral (mm²)",
            title="Controlled comparisons",
        )
        axes[2].legend()
        _save(figure, output, "neuron_glioma_talk")


def neuron_glioma_example(output: Path) -> dict:
    """Compare three nested assumptions and a small prescribed sensitivity grid."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    coordinates, initial, drive = neuron_glioma_construction()
    parameters = NeuronGliomaParameters()
    cases = {
        "baseline": replace(parameters, signal_growth_coupling=0, tumor_signal_feedback_per_day=0),
        "one_way": replace(parameters, tumor_signal_feedback_per_day=0),
        "feedback": parameters,
    }
    trajectories = {
        key: simulate_neuron_glioma(initial, drive, drive, params, 1, 1, 0.1, 200)
        for key, params in cases.items()
    }
    baseline = trajectories["baseline"]["density_integral_mm2"][-1]
    coupling = [0.0, 0.75, 1.5]
    feedback = [0.0, 0.06, 0.12]
    sensitivity = np.zeros((len(feedback), len(coupling)))
    for row, beta in enumerate(feedback):
        for column, kappa in enumerate(coupling):
            trajectory = simulate_neuron_glioma(
                initial,
                drive,
                drive,
                replace(
                    parameters, signal_growth_coupling=kappa, tumor_signal_feedback_per_day=beta
                ),
                1,
                1,
                0.1,
                200,
            )
            sensitivity[row, column] = trajectory["density_integral_mm2"][-1] / baseline
    fine = simulate_neuron_glioma(initial, drive, drive, parameters, 1, 1, 0.05, 400)
    coarse_integral = trajectories["feedback"]["density_integral_mm2"][-1]
    fine_integral = fine["density_integral_mm2"][-1]
    summary = {
        "evidence_type": "synthetic",
        "coordinate_space": "constructed 61 by 61 plane; 1 mm grid, not patient space",
        "state_meanings": {
            "density": "normalized density, not MRI intensity or measured cell count",
            "signal": "slow activity-associated growth-signal index, not Hz or voltage",
            "external_drive": "prescribed dimensionless spatial field",
        },
        "equations": [
            "dc/dt = div(D grad c) + rho*(1+kappa*a)*c*(1-c)",
            "da/dt = (b-a)/tau + beta*c*(1-a)",
        ],
        "solver": "synchronous explicit Euler; no clipping",
        "boundary": "no flux for density; signal has no transport",
        "parameters": {
            "spacing_mm": 1.0,
            "dt_days": 0.1,
            "elapsed_days": 20,
            "cases": {key: asdict(value) for key, value in cases.items()},
        },
        "initial_density_integral_mm2": float(initial.sum()),
        "final_density_integral_mm2": {
            key: float(value["density_integral_mm2"][-1]) for key, value in trajectories.items()
        },
        "final_density_weighted_signal": {
            key: float(value["density_weighted_signal"][-1]) for key, value in trajectories.items()
        },
        "feedback_to_baseline_integral_ratio": float(coarse_integral / baseline),
        "feedback_to_one_way_integral_ratio": float(
            coarse_integral / trajectories["one_way"]["density_integral_mm2"][-1]
        ),
        "step_halving_relative_integral_difference": float(
            abs(coarse_integral - fine_integral) / fine_integral
        ),
        "sensitivity": {
            "growth_coupling": coupling,
            "feedback_per_day": feedback,
            "integral_ratio_to_baseline": sensitivity.tolist(),
        },
        "omitted": [
            "explicit neurons and synapses",
            "electrophysiology",
            "immune dynamics",
            "MRI forward model",
            "treatment",
        ],
        "calibration": "not_performed",
        "clinical_response": "not_assessed",
        "biological_motivation_dois": ["10.1038/s41586-019-1563-y", "10.1038/s41593-025-02149-0"],
    }
    figure, axes = plt.subplots(2, 2, figsize=(9.5, 6.7), constrained_layout=True)
    for axis, key, title in zip(
        axes[0], ("baseline", "feedback"), ("Baseline density", "Coupled density"), strict=True
    ):
        im = axis.imshow(
            trajectories[key]["density"].T,
            origin="lower",
            extent=(-30.5, 30.5, -30.5, 30.5),
            vmin=0,
            vmax=1,
            cmap="magma",
        )
        axis.set(
            xlabel="Constructed x (mm)",
            ylabel="Constructed y (mm)",
            title=title,
            xlim=(-20, 20),
            ylim=(-20, 20),
        )
        figure.colorbar(im, ax=axis, shrink=0.75).set_label("Normalized density")
    delta = trajectories["feedback"]["signal"] - drive
    im = axes[1, 0].imshow(
        delta.T, origin="lower", extent=(-30.5, 30.5, -30.5, 30.5), vmin=0, vmax=0.3, cmap="viridis"
    )
    axes[1, 0].set(
        xlabel="Constructed x (mm)",
        ylabel="Constructed y (mm)",
        title="Signal change with feedback",
        xlim=(-20, 20),
        ylim=(-20, 20),
    )
    figure.colorbar(im, ax=axes[1, 0], shrink=0.75).set_label("Change in signal index")
    for key, title, color in zip(
        cases, ("Baseline", "One-way", "Feedback"), ("#555555", "#31858f", "#d67645"), strict=True
    ):
        axes[1, 1].plot(
            trajectories[key]["time_days"],
            trajectories[key]["density_integral_mm2"],
            label=title,
            color=color,
        )
    axes[1, 1].set(
        xlabel="Prescribed elapsed time (days)",
        ylabel="Density integral (mm²)",
        title="Three nested assumptions",
    )
    axes[1, 1].legend()
    figure.suptitle("Synthetic neuron-glioma model after 20 prescribed days")
    _save(figure, output, "neuron_glioma")
    figure, axis = plt.subplots(figsize=(6.5, 4), constrained_layout=True)
    im = axis.imshow(
        sensitivity, origin="lower", cmap="YlOrBr", vmin=1, vmax=float(sensitivity.max())
    )
    axis.set_xticks(range(len(coupling)), [str(value) for value in coupling])
    axis.set_yticks(range(len(feedback)), [str(value) for value in feedback])
    axis.set(
        xlabel="Prescribed signal-to-growth coupling κ",
        ylabel="Prescribed tumor-to-signal rate β (/day)",
        title="Synthetic sensitivity, not a patient effect",
    )
    for row in range(len(feedback)):
        for column in range(len(coupling)):
            axis.text(
                column,
                row,
                f"{sensitivity[row, column]:.2f}",
                ha="center",
                va="center",
                color="black",
            )
    figure.colorbar(im, ax=axis).set_label("Final density integral / baseline")
    _save(figure, output, "neuron_glioma_sensitivity")
    _talk_views(output, None, None, trajectories)
    np.savez_compressed(
        output / "synthetic_neuron_glioma.npz",
        initial=initial,
        drive=drive,
        baseline=trajectories["baseline"]["density"],
        one_way=trajectories["one_way"]["density"],
        feedback=trajectories["feedback"]["density"],
        signal=trajectories["feedback"]["signal"],
    )
    np.savetxt(
        output / "neuron_glioma_traces.tsv",
        np.column_stack(
            [
                trajectories["baseline"]["time_days"],
                *[value["density_integral_mm2"] for value in trajectories.values()],
            ]
        ),
        delimiter="\t",
        header="time_days\tbaseline_integral_mm2\tone_way_integral_mm2\tfeedback_integral_mm2",
        comments="",
    )
    _write(output / "neuron_glioma.json", summary)
    return summary
