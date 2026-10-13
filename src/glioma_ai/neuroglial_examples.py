"""Generated neuroglial teaching figures, with prescribed physical units."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from glioma_ai.neuroglial import (
    field_from_potential,
    integrate_potassium,
    potassium_equilibrium_mV,
)


def _save(figure, output: Path, stem: str) -> None:
    figure.savefig(output / f"{stem}.png", dpi=180, bbox_inches="tight")
    figure.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)


def astrocyte_example(output: Path) -> dict:
    """Compare prescribed clearance rates under identical K release pulses."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    dt, duration = 0.01, 24
    interval_start = np.arange(round(duration / dt)) * dt
    release = np.where(
        ((interval_start >= 2) & (interval_start < 6))
        | ((interval_start >= 10) & (interval_start < 14)),
        0.6,
        0,
    )
    rates = {"reference": 0.8, "reduced": 0.2, "zero_astro": 0.0}
    traces = {name: integrate_potassium(release, dt, rate, 0.1) for name, rate in rates.items()}
    basal, intracellular, temperature = 3.0, 140.0, 37.0
    equilibrium = float(potassium_equilibrium_mV(basal, intracellular, temperature))
    shifts = {
        name: potassium_equilibrium_mV(basal + trace["excess_mM"], intracellular, temperature)
        - equilibrium
        for name, trace in traces.items()
    }
    # With equal total clearance, different attribution produces the same trace.
    alternative = integrate_potassium(release, dt, 0.2, 0.7)
    ambiguity_error = float(
        np.max(np.abs(alternative["excess_mM"] - traces["reference"]["excess_mM"]))
    )
    balance_error = max(
        float(
            np.max(
                np.abs(
                    trace["excess_mM"]
                    + trace["astro_cleared_mM"]
                    + trace["other_cleared_mM"]
                    - trace["cumulative_release_mM"]
                )
            )
        )
        for trace in traces.values()
    )
    summary = {
        "evidence_type": "synthetic",
        "model": "one-compartment excess extracellular K; piecewise-constant input",
        "equation": "dk/dt = q - (lambda_astro + lambda_other) k",
        "solver": "exact constant-input solution per interval; no clipping",
        "parameters": {
            "dt_s": dt,
            "duration_s": duration,
            "release_mM_per_s": 0.6,
            "release_intervals_s": [[2, 6], [10, 14]],
            "astro_clearance_per_s": rates,
            "other_clearance_per_s": 0.1,
            "baseline_extracellular_K_mM": basal,
            "fixed_intracellular_K_mM": intracellular,
            "temperature_C": temperature,
        },
        "peak_excess_K_mM": {
            name: float(trace["excess_mM"].max()) for name, trace in traces.items()
        },
        "peak_K_equilibrium_shift_mV": {name: float(value.max()) for name, value in shifts.items()},
        "flux_balance_max_absolute_error_mM": balance_error,
        "equal_total_clearance_max_trace_difference_mM": ambiguity_error,
        "interpretation": "prescribed clearance changes excess K and ideal K equilibrium voltage",
        "limitations": [
            "No measured astrocyte impairment, glioma density, membrane voltage or cognitive score",
            "No Kir4.1 channel kinetics, intracellular storage, spatial buffering or rerelease",
            "No LFP forward model and no connection to the day-scale growth signal",
            "Clearance attribution cannot be identified from this K trace alone",
        ],
        "biological_motivation_doi": "10.1113/jphysiol.2013.261735",
        "biological_calibration": "not_performed",
    }
    with plt.rc_context({"font.size": 12, "axes.titlesize": 13}):
        figure, axes = plt.subplots(1, 2, figsize=(10.5, 3.7), constrained_layout=True)
        for name, label, color in (
            ("reference", "Prescribed reference clearance", "#31858f"),
            ("reduced", "Reduced astrocytic clearance", "#cf704b"),
            ("zero_astro", "Zero astrocytic clearance", "#6d6d6d"),
        ):
            trace = traces[name]
            axes[0].plot(trace["time_s"], trace["excess_mM"], label=label, color=color)
            axes[1].plot(trace["time_s"], shifts[name], color=color)
        for axis in axes:
            for start, end in ((2, 6), (10, 14)):
                axis.axvspan(start, end, color="#dee8ec", alpha=0.6, zorder=-1)
            axis.set_xlabel("Prescribed elapsed time (s)")
        axes[0].set(title="Same release, different clearance", ylabel="Excess extracellular K (mM)")
        axes[0].legend(fontsize=9, loc="upper right")
        axes[1].set(title="Ideal K-selective equilibrium", ylabel="Change in E_K (mV)")
        _save(figure, output, "astrocyte_potassium")
    np.savez_compressed(
        output / "synthetic_potassium.npz",
        time_s=traces["reference"]["time_s"],
        release_mM_per_s=release,
        **{f"{name}_excess_mM": trace["excess_mM"] for name, trace in traces.items()},
        **{f"{name}_equilibrium_shift_mV": shift for name, shift in shifts.items()},
    )
    (output / "astrocyte_potassium.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def lfp_field_example(output: Path) -> dict:
    """Two prescribed spatial sinusoids share amplitude but not electric field."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    positions = np.linspace(-5, 5, 1001)
    wavelengths, amplitude = (10.0, 2.5), 100.0
    potentials = np.array([amplitude * np.sin(2 * np.pi * positions / w) for w in wavelengths])
    field = field_from_potential(potentials, positions)
    analytic = np.array(
        [
            -amplitude * 1e-6 * 2 * np.pi / (w * 1e-3) * np.cos(2 * np.pi * positions / w)
            for w in wavelengths
        ]
    )
    summary = {
        "evidence_type": "synthetic",
        "coordinate_space": "prescribed 1D sampling line in mm, not cortical anatomy",
        "potential_unit": "microvolt",
        "field_unit": "V/m",
        "parameters": {"amplitude_uV": amplitude, "wavelengths_mm": list(wavelengths)},
        "peak_analytic_field_V_per_m": np.max(np.abs(analytic), axis=1).tolist(),
        "derivative_max_absolute_error_V_per_m": float(np.max(np.abs(field - analytic))),
        "field_ratio_at_zero": float(field[1, 500] / field[0, 500]),
        "potential_at_zero_uV": potentials[:, 500].tolist(),
        "interpretation": "equal potential amplitudes do not imply equal field gradients",
        "limitations": [
            "Not a recorded LFP or a generated source-current/volume-conductor model",
            "Only one field component; no intracellular or membrane-field inference",
            "No ephaptic, microtubule, glioma-growth or cognition effect is computed",
            "Sampling, noise, conductivity and electrode referencing matter in real recordings",
        ],
        "biophysical_context_doi": "10.1038/nrn3241",
    }
    with plt.rc_context({"font.size": 12, "axes.titlesize": 13}):
        figure, axes = plt.subplots(1, 2, figsize=(10.5, 3.7), constrained_layout=True)
        for index, color in enumerate(("#31858f", "#cf704b")):
            label = f"Wavelength {wavelengths[index]:g} mm"
            axes[0].plot(positions, potentials[index], color=color, label=label)
            axes[1].plot(positions, field[index], color=color)
        axes[0].set(title="Same prescribed voltage amplitude", ylabel="Potential (µV)")
        axes[0].legend(fontsize=10)
        axes[1].set(title="Different spatial gradients", ylabel="One field component (V/m)")
        for axis in axes:
            axis.set_xlabel("Prescribed position (mm)")
            axis.axhline(0, color="#cccccc", linewidth=0.6)
        _save(figure, output, "lfp_field")
    np.savez_compressed(
        output / "synthetic_lfp_field.npz",
        positions_mm=positions,
        potential_uV=potentials,
        field_V_per_m=field,
    )
    (output / "lfp_field.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
