"""Tissue-guided, axis-aligned anisotropic growth on a constructed coronal phantom.

The phantom is drawn from ellipses and bands in code. It is not an atlas, a
patient image, a registered template or a segmentation; its labels and fibre
directions are teaching assumptions. The state is the same normalized density
proxy as in growth_model, not MRI intensity or a cell count.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.growth_model import DensityRun, simulate_density_2d

OUTSIDE, CSF, GREY, WHITE = 0, 1, 2, 3
TISSUE_NAMES = {OUTSIDE: "outside brain", CSF: "CSF", GREY: "grey matter", WHITE: "white matter"}
ISOTROPIC, LEFT_RIGHT, INFERIOR_SUPERIOR = 0, 1, 2
FIBRE_NAMES = {
    ISOTROPIC: "no dominant direction",
    LEFT_RIGHT: "left-right (callosal)",
    INFERIOR_SUPERIOR: "inferior-superior (projection)",
}


@dataclass(frozen=True)
class CoronalPhantom:
    """Cell-centred labels indexed [i, j] = (x_mm[i], y_mm[j]).

    x increases toward the patient's LEFT and y toward SUPERIOR. Plotting x to the
    right therefore shows the patient's left on the viewer's right (radiological).
    """

    x_mm: NDArray[np.float64]
    y_mm: NDArray[np.float64]
    tissue: NDArray[np.int8]
    fibre: NDArray[np.int8]
    spacing_mm: float

    @property
    def extent(self) -> tuple[float, float, float, float]:
        h = self.spacing_mm / 2
        return (self.x_mm[0] - h, self.x_mm[-1] + h, self.y_mm[0] - h, self.y_mm[-1] + h)

    @property
    def brain(self) -> NDArray[np.bool_]:
        return (self.tissue == GREY) | (self.tissue == WHITE)


def callosal_centre_mm(x_mm: ArrayLike) -> NDArray[np.float64]:
    """Centre line of the constructed corpus callosum and its lateral radiation."""
    x = np.asarray(x_mm, dtype=float)
    return 9.0 + 0.006 * x * x


def coronal_phantom(spacing_mm: float = 1.0) -> CoronalPhantom:
    """Construct a 140 x 110 mm coronal slice at roughly parietal/callosal level.

    Cortical ribbon (about 3.5 mm, with a sinusoidal gyral outline), subarachnoid
    CSF rim, a midline CSF barrier (interhemispheric fissure above, septal and
    third-ventricle CSF below), lateral ventricles, Sylvian fissures, thalamic grey
    matter, corpus callosum with left-right fibres and corona radiata with
    inferior-superior fibres. The hemispheres connect only through the corpus
    callosum. Proportions are approximate and not from any subject.
    """
    h = float(spacing_mm)
    if not np.isfinite(h) or not 0.25 <= h <= 2:
        raise ValueError("Spacing must be between 0.25 and 2 mm.")
    x_mm = np.arange(-70, 70 + h / 2, h)
    y_mm = np.arange(-55, 55 + h / 2, h)
    x, y = np.meshgrid(x_mm, y_mm, indexing="ij")
    u, v = x / 64.0, (y + 2.0) / 50.0
    radius = np.hypot(u, v)
    gyral = radius - 0.03 * np.sin(16 * np.arctan2(v, u))
    tissue = np.full(x.shape, OUTSIDE, dtype=np.int8)
    tissue[gyral <= 1.05] = CSF
    tissue[gyral <= 1.0] = GREY
    tissue[gyral <= 0.93] = WHITE
    centre = callosal_centre_mm(x)
    callosum = (np.abs(y - centre) <= 3.5) & (np.abs(x) <= 42) & (gyral <= 0.93)
    inside = gyral <= 1.05
    medial = (np.abs(x) <= 5) & ~callosum & (gyral <= 1.0) & ((y >= 13) | (y <= -24))
    tissue[medial] = GREY
    sylvian = (np.abs(np.abs(x) - (40 + 2 * (-10 - y))) <= 1.2) & (y <= -10) & (y >= -21)
    lining = (np.abs(np.abs(x) - (40 + 2 * (-10 - y))) <= 3.5) & (y <= -8) & (y >= -23)
    tissue[lining & (gyral <= 1.0)] = GREY
    tissue[sylvian & inside] = CSF
    tissue[((np.abs(x) - 9) / 7.5) ** 2 + ((y + 16) / 7) ** 2 <= 1] = GREY
    tissue[((np.abs(x) - 9) / 5.5) ** 2 + ((y + 1) / 6) ** 2 <= 1] = CSF
    tissue[(np.abs(x) <= 1.5) & inside] = CSF
    tissue[callosum] = WHITE
    fibre = np.full(x.shape, ISOTROPIC, dtype=np.int8)
    fibre[callosum] = LEFT_RIGHT
    projection = (
        (tissue == WHITE)
        & ~callosum
        & (np.abs(x) >= 16)
        & (np.abs(x) <= 44)
        & (y >= -30)
        & (y <= centre - 3.5)
    )
    fibre[projection] = INFERIOR_SUPERIOR
    return CoronalPhantom(x_mm, y_mm, tissue, fibre, h)


def tissue_fields(
    phantom: CoronalPhantom,
    grey_mm2_per_day: float,
    white_to_grey: float,
    fibre_ratio: float,
    rho_per_day: float,
) -> tuple[NDArray, NDArray, NDArray]:
    """Diagonal diffusion tensor (D_xx, D_yy) and growth field rho on the phantom.

    Grey matter: D_g in both directions. White matter: D_w = r D_g. Along a
    labelled fibre direction the coefficient is multiplied by a, the other
    direction stays D_w. CSF and outside: D = 0 and rho = 0 (a no-flux barrier).
    """
    d_g, r, a, rho = map(float, (grey_mm2_per_day, white_to_grey, fibre_ratio, rho_per_day))
    if not np.isfinite([d_g, r, a, rho]).all() or d_g < 0 or rho < 0 or r < 1 or a < 1:
        raise ValueError("Require D_g >= 0, rho >= 0, white/grey ratio >= 1, fibre ratio >= 1.")
    base = np.where(phantom.tissue == GREY, d_g, 0.0)
    base = np.where(phantom.tissue == WHITE, r * d_g, base)
    d_xx = np.where(phantom.fibre == LEFT_RIGHT, a * base, base)
    d_yy = np.where(phantom.fibre == INFERIOR_SUPERIOR, a * base, base)
    return d_xx, d_yy, np.where(phantom.brain, rho, 0.0)


def _harmonic_faces(d: NDArray, axis: int) -> NDArray:
    left = d[:-1, :] if axis == 0 else d[:, :-1]
    right = d[1:, :] if axis == 0 else d[:, 1:]
    total = left + right
    return np.divide(2 * left * right, total, out=np.zeros_like(total), where=total > 0)


def anisotropic_step_limit(
    d_xx: ArrayLike, d_yy: ArrayLike, dx_mm: float = 1.0, dy_mm: float = 1.0
) -> float:
    """Largest step keeping every diffusion update a convex combination, in days.

    Uses the harmonic face coefficients actually applied, cell by cell, so it is
    the exact positivity condition of this scheme rather than a global bound.
    """
    dxx, dyy = np.asarray(d_xx, dtype=float), np.asarray(d_yy, dtype=float)
    dx, dy = float(dx_mm), float(dy_mm)
    if dxx.ndim != 2 or dxx.shape != dyy.shape or min(dxx.shape) < 3:
        raise ValueError("D_xx and D_yy must be planes of equal shape, at least 3 x 3.")
    if not np.isfinite(dxx).all() or not np.isfinite(dyy).all() or min(dxx.min(), dyy.min()) < 0:
        raise ValueError("Diffusivities must be finite and nonnegative.")
    if not np.isfinite([dx, dy]).all() or min(dx, dy) <= 0:
        raise ValueError("Spacings must be positive finite millimetres.")
    fx, fy = _harmonic_faces(dxx, 0) / dx**2, _harmonic_faces(dyy, 1) / dy**2
    weight = np.zeros_like(dxx)
    weight[:-1, :] += fx
    weight[1:, :] += fx
    weight[:, :-1] += fy
    weight[:, 1:] += fy
    return np.inf if weight.max() == 0 else float(1 / weight.max())


def simulate_tissue_density_2d(
    initial: ArrayLike,
    d_xx_mm2_per_day: ArrayLike,
    d_yy_mm2_per_day: ArrayLike,
    rho_per_day: ArrayLike,
    days: ArrayLike,
    *,
    dx_mm: float = 1.0,
    dy_mm: float = 1.0,
    dt_days: float = 0.2,
) -> DensityRun:
    """Exact half reaction, conservative Euler diffusion with a diagonal tensor, half reaction.

    dc/dt = d/dx(D_xx dc/dx) + d/dy(D_yy dc/dy) + rho(x, y) c (1 - c).
    Face coefficients are harmonic means, so a face next to a D = 0 cell carries
    no flux: CSF and the outside act as no-flux barriers, as does the outer
    rectangle. Fibre directions are restricted to the image axes; there are no
    cross-derivative terms. Steps above the positivity limit are rejected.
    """
    c = np.array(initial, dtype=float, copy=True)
    dxx = np.asarray(d_xx_mm2_per_day, dtype=float)
    dyy = np.asarray(d_yy_mm2_per_day, dtype=float)
    rho = np.broadcast_to(np.asarray(rho_per_day, dtype=float), c.shape)
    times = np.asarray(days, dtype=float)
    dx, dy, dt = float(dx_mm), float(dy_mm), float(dt_days)
    if c.ndim != 2 or dxx.shape != c.shape or dyy.shape != c.shape:
        raise ValueError("Initial density, D_xx and D_yy must be planes of equal shape.")
    if not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
        raise ValueError("Initial normalized density must be finite and in [0, 1].")
    if not np.isfinite(rho).all() or rho.min() < 0:
        raise ValueError("Growth rates must be finite and nonnegative.")
    if (
        times.ndim != 1
        or len(times) < 2
        or not np.isfinite(times).all()
        or times[0] != 0
        or np.any(np.diff(times) <= 0)
    ):
        raise ValueError("Snapshot days must start at zero and increase strictly.")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("Time step must be positive and finite.")
    limit = anisotropic_step_limit(dxx, dyy, dx, dy)
    if dt > limit:
        raise ValueError(f"Time step {dt:g} exceeds the positivity limit {limit:g} days.")
    fx, fy = _harmonic_faces(dxx, 0) / dx, _harmonic_faces(dyy, 1) / dy
    area = dx * dy
    start_mass = float(c.sum() * area)
    snapshots, mass, reaction = [c.copy()], [start_mass], [0.0]
    gain, balance_error, steps, largest = 0.0, 0.0, 0, 0.0
    divergence = np.empty_like(c)

    def react(values: NDArray, decay: NDArray) -> NDArray:
        return np.divide(
            values, values + (1 - values) * decay, out=np.zeros_like(values), where=values > 0
        )

    for start, end in zip(times[:-1], times[1:], strict=True):
        count = int(np.ceil((end - start) / dt))
        step = float((end - start) / count)
        decay = np.exp(-rho * step / 2)
        for _ in range(count):
            half = react(c, decay)
            flux_x = fx * np.diff(half, axis=0) / dx
            flux_y = fy * np.diff(half, axis=1) / dy
            divergence.fill(0.0)
            divergence[:-1, :] += flux_x
            divergence[1:, :] -= flux_x
            divergence[:, :-1] += flux_y
            divergence[:, 1:] -= flux_y
            moved = half + step * divergence
            if moved.min() < 0 or moved.max() > 1:
                raise ArithmeticError("Diffusion violated the density bounds; no clipping applied.")
            final = react(moved, decay)
            gain += float(((half - c).sum() + (final - moved).sum()) * area)
            c = final
            balance_error = max(balance_error, abs(float(c.sum() * area) - start_mass - gain))
        steps += count
        largest = max(largest, step)
        snapshots.append(c.copy())
        mass.append(float(c.sum() * area))
        reaction.append(gain)
    return DensityRun(
        times.copy(),
        np.stack(snapshots),
        np.asarray(mass),
        np.asarray(reaction),
        balance_error,
        dx,
        dy,
        steps,
        largest,
        limit,
    )


def tumour_seed(
    phantom: CoronalPhantom,
    centre_mm: tuple[float, float] = (38.0, 27.0),
    radius_mm: float = 5.0,
    occupancy: float = 0.65,
) -> NDArray[np.float64]:
    """Prescribed initial occupancy in a disk, restricted to brain tissue.

    The default centre lies in left parietal subcortical white matter, touching
    the lateral callosal radiation. It is a constructed seed, not a lesion.
    """
    x, y = np.meshgrid(phantom.x_mm, phantom.y_mm, indexing="ij")
    disk = (x - centre_mm[0]) ** 2 + (y - centre_mm[1]) ** 2 <= radius_mm**2
    return float(occupancy) * (disk & phantom.brain)


def contralateral_summary(phantom: CoronalPhantom, run: DensityRun, threshold: float = 0.1) -> dict:
    """Density proxy in the patient's right hemisphere (x < 0) over time.

    The midline split is a geometric convention on the phantom, not an
    anatomical parcellation.
    """
    right = phantom.x_mm < 0
    contra = run.density[:, right, :].sum(axis=(1, 2)) * run.dx_mm * run.dy_mm
    reached = (run.density[:, right, :] >= threshold).any(axis=(1, 2))
    first = run.days[np.argmax(reached)] if reached.any() else None
    return {
        "contralateral_integral_mm2": contra,
        "contralateral_fraction": np.divide(
            contra, run.integral_mm2, out=np.zeros_like(contra), where=run.integral_mm2 > 0
        ),
        "first_day_at_threshold": None if first is None else float(first),
        "threshold": float(threshold),
    }


def tissue_scenarios(
    phantom: CoronalPhantom,
    *,
    grey_mm2_per_day: float = 0.1,
    white_to_grey: float = 5.0,
    fibre_ratio: float = 2.0,
    rho_per_day: float = 0.035,
    days: ArrayLike | None = None,
    seed: NDArray | None = None,
) -> dict[str, tuple[DensityRun, tuple[NDArray, NDArray, NDArray]]]:
    """Three nested assumptions, switching on one tissue effect at a time.

    Uniform tissue uses D_g everywhere in brain (r = a = 1); it is slower overall,
    not a matched-mean control. The time step is 0.9 of the positivity limit,
    capped at 0.2 day, and recorded in each run.
    """
    initial = tumour_seed(phantom) if seed is None else seed
    days = np.arange(0, 366, 5, dtype=float) if days is None else days
    settings = {
        "Uniform tissue, isotropic": (1.0, 1.0),
        "Grey/white contrast, isotropic": (white_to_grey, 1.0),
        "Grey/white contrast + fibre anisotropy": (white_to_grey, fibre_ratio),
    }
    runs = {}
    for name, (r, a) in settings.items():
        fields = tissue_fields(phantom, grey_mm2_per_day, r, a, rho_per_day)
        limit = anisotropic_step_limit(fields[0], fields[1], phantom.spacing_mm, phantom.spacing_mm)
        dt = min(0.2, 0.9 * limit)
        run = simulate_tissue_density_2d(
            initial,
            *fields,
            days,
            dx_mm=phantom.spacing_mm,
            dy_mm=phantom.spacing_mm,
            dt_days=dt,
        )
        runs[name] = (run, fields)
    return runs


def tissue_solver_controls() -> dict:
    """Reduction to the isotropic solver, barrier, conservation and an anisotropic mode.

    For c = 0.4 + 0.2 exp(-(D_xx + D_yy)(pi/L)^2 t) cos(pi x/L) cos(pi y/L) on
    [0, L]^2 with constant D_xx != D_yy and zero normal flux, the error should
    fall with refinement (dt proportional to h^2). Numerical checks only.
    """
    rng = np.random.default_rng(2026)
    start = rng.uniform(0.05, 0.9, (13, 15))
    reference = simulate_density_2d(start, 0.3, 0.05, [0, 2, 6], dt_days=0.2)
    constant = np.full(start.shape, 0.3)
    same = simulate_tissue_density_2d(start, constant, constant, 0.05, [0, 2, 6], dt_days=0.2)
    dxx, dyy = rng.uniform(0.1, 0.9, start.shape), rng.uniform(0.1, 0.9, start.shape)
    barrier = np.zeros(start.shape, dtype=bool)
    barrier[6, :] = True
    dxx[barrier] = dyy[barrier] = 0.0
    blocked = np.where(barrier, 0.0, start)
    conserved = simulate_tissue_density_2d(blocked, dxx, dyy, 0.0, [0, 5], dt_days=0.05)
    left = blocked[:6].sum(), conserved.density[-1][:6].sum()
    convergence = []
    length, d_xx, d_yy, duration = 20.0, 0.6, 0.15, 5.0
    for n in (15, 30, 60):
        h = length / n
        x = (np.arange(n) + 0.5) * h
        mode = np.cos(np.pi * x[:, None] / length) * np.cos(np.pi * x[None, :] / length)
        dt = duration / n**2
        run = simulate_tissue_density_2d(
            0.4 + 0.2 * mode,
            np.full((n, n), d_xx),
            np.full((n, n), d_yy),
            0.0,
            [0, duration],
            dx_mm=h,
            dy_mm=h,
            dt_days=dt,
        )
        truth = 0.4 + 0.2 * np.exp(-(d_xx + d_yy) * (np.pi / length) ** 2 * duration) * mode
        convergence.append(
            {
                "n": n,
                "spacing_mm": h,
                "dt_days_max": dt,
                "rms_error": float(np.sqrt(np.mean((run.density[-1] - truth) ** 2))),
            }
        )
    return {
        "isotropic_reduction_max_difference": float(
            np.max(np.abs(same.density - reference.density))
        ),
        "barrier_cells_max_density": float(conserved.density[:, barrier].max()),
        "barrier_side_mass_change": float(abs(left[1] - left[0])),
        "heterogeneous_anisotropic_mass_error_mm2": float(
            abs(conserved.integral_mm2[-1] - conserved.integral_mm2[0])
        ),
        "anisotropic_cosine_refinement": convergence,
        "verification_scope": "analytic/numerical controls, not clinical validation",
    }
