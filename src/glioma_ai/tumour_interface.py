"""The tumour-brain interface on one line: what an MRI boundary does and does not contain.

A one-dimensional Fisher--Kolmogorov front is grown from the tumour centre until
its contrast-enhancing (T1Gd) boundary reaches a prescribed radius. The T1Gd and
T2/FLAIR boundaries are read as 80% and 16% of the maximum normalized
tumour-cell density, after Swanson et al. (2008), as in notebook 03. Diffusivities
are the median and range ends reported by Wang et al. (2009) for 32 untreated
glioblastomas; the proliferation rate is their median. Regions A, B and C are
constructed bands along the line, not anatomical structures. The geometry is
planar: fractions are fractions of the cells on this line, not tumour volumes,
and nothing here is a patient estimate or a treatment margin recommendation.
"""

import numpy as np

from glioma_ai.growth import fisher_step, threshold_extents

T1GD_FRACTION = 0.80
T2_FRACTION = 0.16
TRACE_FRACTION = 0.01
READING_SOURCE = "Swanson KR et al., Br J Cancer 98:113-119 (2008), doi:10.1038/sj.bjc.6604125"
COEFFICIENT_SOURCE = (
    "Wang CH et al., Cancer Res 69:9133-9140 (2009), doi:10.1158/0008-5472.CAN-08-3863; "
    "D median 29.7 mm^2/year (range 3.2-468.9), rho median 15/year"
)
DIFFUSIVITIES_MM2_PER_YEAR = {"nodular": 3.2, "median": 29.7, "diffuse": 468.9}
RHO_PER_YEAR = 15.0
REGIONS_MM = {"A": (0.0, 25.0), "B": (25.0, 35.0), "C": (35.0, 120.0)}
LEVELS = {"T1Gd": T1GD_FRACTION, "T2/FLAIR": T2_FRACTION, "1%": TRACE_FRACTION}


def _grow_to_radius(
    diffusivity_mm2_per_day: float,
    rho_per_day: float,
    radius_mm: float,
    dx_mm: float,
    span_mm: float,
    seed_mm: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    position = np.arange(0.0, span_mm + dx_mm / 2, dx_mm)
    cells = np.where(position <= seed_mm, 0.5, 0.0)
    diffusivity = np.full_like(position, diffusivity_mm2_per_day)
    dt = min(0.4 * dx_mm**2 / (2 * diffusivity_mm2_per_day), 0.05 / rho_per_day)
    time, check = 0.0, max(1, int(0.5 / dt))
    while True:
        for _ in range(check):
            cells = fisher_step(cells, diffusivity, rho_per_day, dx_mm, dt)
            time += dt
        if threshold_extents(position, cells, T1GD_FRACTION)["right"] >= radius_mm:
            return position, cells, time
        if cells[-1] > 1e-6:
            raise ValueError("The front reached the end of the line; increase span_mm.")


def _share(position: np.ndarray, cells: np.ndarray, start: float, stop: float = np.inf) -> float:
    steps = 0.5 * (cells[1:] + cells[:-1]) * np.diff(position)
    cumulative = np.concatenate([[0.0], np.cumsum(steps)])
    low, high = np.interp([start, min(stop, position[-1])], position, cumulative)
    return float((high - low) / cumulative[-1])


def iceberg_profiles(
    diffusivities_mm2_per_year: dict | None = None,
    rho_per_year: float = RHO_PER_YEAR,
    t1gd_radius_mm: float = 15.0,
    margin_mm: float = 15.0,
    regions_mm: dict | None = None,
    dx_mm: float = 0.1,
    span_mm: float = 120.0,
    seed_mm: float = 1.0,
) -> dict:
    """Grow each case until its T1Gd boundary is at ``t1gd_radius_mm``, then read its boundaries.

    For each case the result gives the density profile, the distance from the
    centre to each reading level, the fraction of the line's cells beyond the
    T2/FLAIR boundary and beyond the T1Gd boundary plus ``margin_mm``, and,
    for each region, the fraction of its length at or above each reading level
    ("hit" at that level) and its share of the cells.
    """
    cases = dict(
        DIFFUSIVITIES_MM2_PER_YEAR
        if diffusivities_mm2_per_year is None
        else diffusivities_mm2_per_year
    )
    regions = dict(REGIONS_MM if regions_mm is None else regions_mm)
    if not cases or any(value <= 0 for value in cases.values()):
        raise ValueError("Diffusivities must be positive.")
    if rho_per_year <= 0 or t1gd_radius_mm <= seed_mm or margin_mm < 0 or dx_mm <= 0:
        raise ValueError("Require rho > 0, radius > seed, margin >= 0 and dx > 0.")
    rho = rho_per_year / 365.0
    results = {}
    for name, diffusivity_per_year in cases.items():
        diffusivity = diffusivity_per_year / 365.0
        position, cells, days = _grow_to_radius(
            diffusivity, rho, t1gd_radius_mm, dx_mm, span_mm, seed_mm
        )
        extents = {
            label: threshold_extents(position, cells, level)["right"]
            for label, level in LEVELS.items()
        }
        involvement = {}
        for region, (start, stop) in regions.items():
            inside = (position >= start) & (position < stop)
            involvement[region] = {
                "cell_share": _share(position, cells, start, stop),
                **{
                    label: float(np.mean(cells[inside] >= level)) for label, level in LEVELS.items()
                },
            }
        results[name] = {
            "diffusivity_mm2_per_year": float(diffusivity_per_year),
            "front_width_mm": float(np.sqrt(diffusivity / rho)),
            "days_to_radius": float(days),
            "position_mm": position,
            "density": cells,
            "extent_mm": extents,
            "invisible_margin_mm": extents["1%"] - extents["T1Gd"],
            "fraction_beyond_flair": _share(position, cells, extents["T2/FLAIR"]),
            "fraction_beyond_margin": _share(position, cells, extents["T1Gd"] + margin_mm),
            "regions": involvement,
        }
    return {
        "cases": results,
        "parameters": {
            "rho_per_year": rho_per_year,
            "t1gd_radius_mm": t1gd_radius_mm,
            "margin_mm": margin_mm,
            "regions_mm": regions,
            "levels": dict(LEVELS),
            "dx_mm": dx_mm,
            "span_mm": span_mm,
            "reading_source": READING_SOURCE,
            "coefficient_source": COEFFICIENT_SOURCE,
            "geometry": "planar line from the tumour centre; no-flux at the centre",
        },
    }


def draw_iceberg(figure, run: dict) -> None:
    """Density on linear and logarithmic axes, with reading levels, the margin and regions."""
    colours = {"nodular": "#2a7f8f", "median": "#555555", "diffuse": "#d95f02"}
    parameters = run["parameters"]
    margin_end = parameters["t1gd_radius_mm"] + parameters["margin_mm"]
    xmax = 75.0
    left, right = figure.subplots(1, 2, sharex=True)
    for axis in (left, right):
        for index, (region, (start, stop)) in enumerate(parameters["regions_mm"].items()):
            axis.axvspan(start, min(stop, xmax), color="0.93" if index % 2 else "white", zorder=0)
            axis.text(
                (start + min(stop, xmax)) / 2,
                1.01,
                f"region {region}",
                transform=axis.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=8,
            )
        axis.axvline(margin_end, color="black", linestyle=":", linewidth=1)
        for name, case in run["cases"].items():
            axis.plot(
                case["position_mm"],
                case["density"],
                color=colours.get(name),
                label=f"{name}: D = {case['diffusivity_mm2_per_year']:g} mm²/year",
            )
        axis.set_xlim(0, xmax)
        axis.set_xlabel("Distance from tumour centre (mm)")
    for label, level in parameters["levels"].items():
        for axis in (left, right):
            axis.axhline(level, color="0.5", linestyle="--", linewidth=0.8)
        right.text(xmax - 1, level * 1.15, label, ha="right", fontsize=8, color="0.3")
    left.set_ylabel("Normalized tumour-cell density")
    left.set_ylim(0, 1.05)
    left.set_title("Linear scale: the visible part", loc="left", fontsize=10, pad=16)
    left.legend(loc="upper right", fontsize=8, frameon=False)
    right.set_yscale("log")
    right.set_ylim(1e-4, 2)
    right.set_title(
        "Log scale: the invisible tail; dotted line = T1Gd + margin",
        loc="left",
        fontsize=10,
        pad=16,
    )
