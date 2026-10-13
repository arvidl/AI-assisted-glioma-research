"""A constructed structural network on the coronal phantom, its lesioning and linear dynamics.

Nodes are grey-matter regions of the phantom in tissue_growth; edges follow the
shortest white-matter path between two regions. Edge weights decay with path
length. Lesions come from the tissue-guided density proxy of notebook 02, so a
tract is weakened where tumour-infiltrated tissue lies on its path. Regional
activity follows a linear, noise-driven network whose functional connectivity
has an exact analytic solution. Everything here is a teaching construction: not
a tractogram, not a patient connectome and not a calibrated model.
"""

import heapq
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.tissue_growth import GREY, LEFT_RIGHT, WHITE, CoronalPhantom

SECTORS = (
    ("medial", "medial parietal (precuneus-like)"),
    ("vertex", "paracentral / superior"),
    ("superior", "superior parietal"),
    ("lateral", "supramarginal / inferior parietal"),
    ("temporal", "superior temporal"),
    ("inferior", "inferior / basal temporal"),
    ("deep", "thalamus"),
)
_ANGLE_EDGES_DEG = (90.0, 62.0, 30.0, 0.0, -35.0, -90.0)


@dataclass(frozen=True)
class PhantomNetwork:
    """Nodes, white-matter paths and distance-dependent weights on one phantom.

    Node order: patient-right sectors then patient-left sectors, each in SECTORS
    order. paths[i][j] lists (ix, iy) grid indices of the tract proxy from node i
    to node j; length_mm[i, j] is its length. weight = exp(-length / decay).
    """

    names: tuple[str, ...]
    descriptions: tuple[str, ...]
    hemisphere: NDArray[np.str_]
    labels: NDArray[np.int16]
    centroid_mm: NDArray[np.float64]
    paths: tuple[tuple[NDArray[np.int64], ...], ...]
    length_mm: NDArray[np.float64]
    weight: NDArray[np.float64]
    decay_mm: float

    @property
    def size(self) -> int:
        return len(self.names)

    @property
    def interhemispheric(self) -> NDArray[np.bool_]:
        return self.hemisphere[:, None] != self.hemisphere[None, :]


def node_labels(phantom: CoronalPhantom) -> tuple[NDArray[np.int16], list[str], list[str], list]:
    """Partition the phantom's grey matter into seven regions per hemisphere.

    Cortical sectors are angular bands of the cortical ribbon around the brain
    centre; the medial wall and the thalamic grey matter are separate regions.
    The names are approximate analogues at a parietal coronal level, not atlas
    labels. Unassigned cells are -1.
    """
    x, y = np.meshgrid(phantom.x_mm, phantom.y_mm, indexing="ij")
    grey = phantom.tissue == GREY
    deep = grey & (((np.abs(x) - 9) / 7.5) ** 2 + ((y + 16) / 7) ** 2 <= 1)
    medial = grey & ~deep & (np.abs(x) <= 5) & (y >= 13)
    angle = np.degrees(np.arctan2((y + 2.0) / 50.0, np.abs(x) / 64.0))
    labels = np.full(x.shape, -1, dtype=np.int16)
    names, descriptions, sides = [], [], []
    for side, mask in (("R", x < 0), ("L", x > 0)):
        for key, description in SECTORS:
            if key == "medial":
                cells = medial & mask
            elif key == "deep":
                cells = deep & mask
            else:
                k = [s for s, _ in SECTORS[1:6]].index(key)
                high, low = _ANGLE_EDGES_DEG[k], _ANGLE_EDGES_DEG[k + 1]
                cells = grey & ~deep & ~medial & mask & (angle <= high) & (angle > low)
            labels[cells] = len(names)
            names.append(f"{side}-{key}")
            descriptions.append(description)
            sides.append(side)
    return labels, names, descriptions, sides


_STEPS = [(di, dj, float(np.hypot(di, dj))) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj]


def _white_matter_paths(labels: NDArray, white: NDArray, source: int, count: int) -> list:
    """Shortest 8-connected paths from one region through white matter to every region.

    Paths leave the source region into white matter, run through white matter
    and end at the first cell of a target region entered from white matter; they
    never pass through other grey matter or CSF, so neighbouring cortical
    sectors connect through the white matter beneath them rather than along the
    ribbon. Unreachable targets return an empty path.
    """
    nx, ny = labels.shape
    distance = np.full(labels.shape, np.inf)
    previous = -np.ones(labels.shape + (2,), dtype=np.int64)
    heap = []
    for i, j in zip(*np.nonzero(labels == source), strict=True):
        distance[i, j] = 0.0
        heap.append((0.0, int(i), int(j)))
    heapq.heapify(heap)
    while heap:
        d, i, j = heapq.heappop(heap)
        if d > distance[i, j]:
            continue
        if labels[i, j] >= 0 and labels[i, j] != source:
            continue
        for di, dj, step in _STEPS:
            a, b = i + di, j + dj
            if not (0 <= a < nx and 0 <= b < ny):
                continue
            if not (white[a, b] or (white[i, j] and labels[a, b] >= 0)):
                continue
            if d + step < distance[a, b]:
                distance[a, b] = d + step
                previous[a, b] = (i, j)
                heapq.heappush(heap, (d + step, a, b))
    paths = []
    for target in range(count):
        cells = np.argwhere(labels == target)
        if target == source or not np.isfinite(distance[tuple(cells.T)]).any():
            paths.append((np.empty((0, 2), dtype=np.int64), np.inf))
            continue
        end = cells[np.argmin(distance[tuple(cells.T)])]
        length = float(distance[tuple(end)])
        route = [tuple(end)]
        while previous[route[-1]][0] >= 0:
            route.append(tuple(previous[route[-1]]))
        paths.append((np.asarray(route[::-1], dtype=np.int64), length))
    return paths


def phantom_network(phantom: CoronalPhantom, decay_mm: float = 40.0) -> PhantomNetwork:
    """Build the constructed network; weight_ij = exp(-L_ij / decay_mm), zero diagonal."""
    if not np.isfinite(decay_mm) or decay_mm <= 0:
        raise ValueError("Decay length must be positive millimetres.")
    labels, names, descriptions, sides = node_labels(phantom)
    n = len(names)
    white = phantom.tissue == WHITE
    x, y = np.meshgrid(phantom.x_mm, phantom.y_mm, indexing="ij")
    centroid = np.array([[x[labels == k].mean(), y[labels == k].mean()] for k in range(n)])
    rows, length = [], np.full((n, n), np.inf)
    for source in range(n):
        found = _white_matter_paths(labels, white, source, n)
        rows.append(tuple(path for path, _ in found))
        length[source] = [value for _, value in found]
    length = np.minimum(length, length.T)
    weight = np.where(np.isfinite(length), np.exp(-length / decay_mm), 0.0)
    np.fill_diagonal(weight, 0.0)
    return PhantomNetwork(
        tuple(names),
        tuple(descriptions),
        np.asarray(sides),
        labels,
        centroid,
        tuple(rows),
        length,
        weight,
        float(decay_mm),
    )


def tract_integrity(
    network: PhantomNetwork,
    density: ArrayLike,
    cavity: ArrayLike | None = None,
    *,
    rule: str = "attenuation",
    damage_length_mm: float = 10.0,
    spacing_mm: float = 1.0,
) -> NDArray[np.float64]:
    """Fraction of each tract assumed intact, from the density proxy along its path.

    "attenuation": exp(-(1/l_d) * sum of c over path cells * spacing), so damage
    accumulates with the infiltrated length; l_d is a teaching choice.
    "max": 1 - (largest c on the path), so one saturated cell cuts the tract.
    A tract crossing a resection cavity (boolean plane) is cut (integrity 0).
    Both rules are stated assumptions: the density proxy is not a measured fibre
    loss. Returns a symmetric matrix with unit diagonal.
    """
    c = np.asarray(density, dtype=float)
    cut = np.zeros(c.shape, dtype=bool) if cavity is None else np.asarray(cavity, dtype=bool)
    if c.shape != network.labels.shape or cut.shape != c.shape:
        raise ValueError("Density and cavity must match the phantom grid.")
    if not np.isfinite(c).all() or c.min() < 0 or c.max() > 1:
        raise ValueError("Density proxy must be finite and in [0, 1].")
    if rule not in ("attenuation", "max"):
        raise ValueError("Rule must be 'attenuation' or 'max'.")
    if not np.isfinite(damage_length_mm) or damage_length_mm <= 0:
        raise ValueError("Damage length must be positive millimetres.")
    n = network.size
    integrity = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            path = network.paths[i][j]
            if len(path) == 0:
                continue
            index = tuple(path.T)
            if cut[index].any():
                value = 0.0
            elif rule == "max":
                value = 1.0 - float(c[index].max())
            else:
                value = float(np.exp(-c[index].sum() * spacing_mm / damage_length_mm))
            integrity[i, j] = integrity[j, i] = value
    return integrity


def resection_cavity(
    phantom: CoronalPhantom, density: ArrayLike, threshold: float = 0.3, side: str = "L"
) -> NDArray[np.bool_]:
    """Cells removed by a constructed resection of the density proxy.

    White matter in one hemisphere (default the patient's left, where the seed
    lies) with density at or above the threshold, sparing the corpus callosum
    and all grey-matter regions. Threshold and sparing rule are teaching
    choices, not a surgical margin or plan.
    """
    c = np.asarray(density, dtype=float)
    if c.shape != phantom.tissue.shape:
        raise ValueError("Density must match the phantom grid.")
    if side not in ("L", "R"):
        raise ValueError("Side must be 'L' or 'R'.")
    x = phantom.x_mm[:, None] * np.ones_like(phantom.y_mm)[None, :]
    hemisphere = x > 0 if side == "L" else x < 0
    white = (phantom.tissue == WHITE) & (phantom.fibre != LEFT_RIGHT)
    return white & hemisphere & (c >= float(threshold))


def callosum_sparing(phantom: CoronalPhantom, density: ArrayLike) -> NDArray[np.float64]:
    """Control: the same density proxy with the corpus callosum assumed uninvolved."""
    c = np.array(density, dtype=float, copy=True)
    c[phantom.fibre == LEFT_RIGHT] = 0.0
    return c


def global_efficiency(weight: ArrayLike) -> float:
    """Mean inverse shortest-path length with edge length 1 / weight (Latora-Marchiori form)."""
    w = np.asarray(weight, dtype=float)
    n = len(w)
    distance = np.divide(1.0, w, out=np.full(w.shape, np.inf), where=w > 0)
    np.fill_diagonal(distance, 0.0)
    for k in range(n):
        distance = np.minimum(distance, distance[:, k : k + 1] + distance[k : k + 1, :])
    off = ~np.eye(n, dtype=bool)
    return float(np.mean(1.0 / distance[off]))


def network_summary(network: PhantomNetwork, weight: ArrayLike) -> dict:
    w = np.asarray(weight, dtype=float)
    cross = network.interhemispheric
    return {
        "total_weight": float(np.triu(w, 1).sum()),
        "interhemispheric_weight": float(np.triu(np.where(cross, w, 0.0), 1).sum()),
        "global_efficiency": global_efficiency(w),
        "node_strength": w.sum(axis=1),
    }


def spectral_radius(weight: ArrayLike) -> float:
    """Largest absolute eigenvalue of a symmetric weight matrix.

    Dividing every scenario by the healthy network's radius keeps one scale, so
    a lesion that removes weight cannot raise the radius (Perron-Frobenius) and
    a stable healthy network stays stable.
    """
    return float(np.max(np.abs(np.linalg.eigvalsh(np.asarray(weight, dtype=float)))))


def linear_fc(scaled: ArrayLike, coupling: float = 0.8, noise: float = 1.0):
    """Exact stationary covariance and correlation of dx/dt = -x + g W x + sigma xi.

    W is a symmetric, nonnegative weight matrix already divided by the healthy
    spectral radius. Time is in units of the node time constant tau and activity
    is dimensionless (not BOLD; no haemodynamic model). For g rho(W) < 1 the
    stationary covariance solves the Lyapunov equation A S + S A^T + sigma^2 I = 0
    with A = g W - I, giving S = (sigma^2 / 2) (I - g W)^-1.
    """
    w = np.asarray(scaled, dtype=float)
    if w.ndim != 2 or w.shape[0] != w.shape[1] or not np.allclose(w, w.T):
        raise ValueError("Weights must form a symmetric square matrix.")
    if np.any(w < 0) or np.any(np.diag(w) != 0):
        raise ValueError("Weights must be nonnegative with a zero diagonal.")
    g, sigma = float(coupling), float(noise)
    if not np.isfinite([g, sigma]).all() or g < 0 or sigma <= 0:
        raise ValueError("Coupling must be nonnegative and noise positive.")
    if g * float(np.max(np.abs(np.linalg.eigvalsh(w)))) >= 1:
        raise ValueError("Unstable: coupling times spectral radius must be below 1.")
    covariance = 0.5 * sigma**2 * np.linalg.inv(np.eye(len(w)) - g * w)
    scale = np.sqrt(np.diag(covariance))
    return covariance, covariance / np.outer(scale, scale)


def simulate_linear(
    scaled: ArrayLike, coupling: float, *, duration: float, dt: float, noise: float = 1.0, seed=0
) -> NDArray[np.float64]:
    """Euler-Maruyama samples of the linear network, starting at rest (time in tau)."""
    w = np.asarray(scaled, dtype=float)
    steps = int(round(duration / dt))
    if steps < 10 or dt <= 0:
        raise ValueError("Need a positive step and at least ten steps.")
    rng = np.random.default_rng(seed)
    drift = np.eye(len(w)) * (1 - dt) + dt * float(coupling) * w
    kicks = rng.standard_normal((steps, len(w))) * float(noise) * np.sqrt(dt)
    x = np.zeros(len(w))
    samples = np.empty((steps, len(w)))
    for k in range(steps):
        x = drift @ x + kicks[k]
        samples[k] = x
    return samples


def euler_maruyama_covariance(scaled: ArrayLike, coupling: float, dt: float, noise=1.0):
    """Exact stationary covariance of the Euler-Maruyama recursion x' = B x + sigma sqrt(dt) n.

    B = (1 - dt) I + dt g W is symmetric, so the discrete Lyapunov equation
    S = B S B^T + sigma^2 dt I is diagonal in B's eigenbasis. As dt -> 0 this
    tends to the continuous covariance; the difference is the step bias.
    """
    w = np.asarray(scaled, dtype=float)
    b, vectors = np.linalg.eigh((1 - dt) * np.eye(len(w)) + dt * float(coupling) * w)
    if np.max(np.abs(b)) >= 1:
        raise ValueError("Euler-Maruyama recursion is not stable for this step.")
    return (vectors * (float(noise) ** 2 * dt / (1 - b**2))) @ vectors.T


def _correlation(covariance: NDArray) -> NDArray:
    scale = np.sqrt(np.diag(covariance))
    return covariance / np.outer(scale, scale)


def linear_controls(scaled: ArrayLike, coupling: float = 0.8) -> dict:
    """Two separate checks of the simulated against the analytic correlation.

    Step bias: exact discrete-time correlation against the continuous one for
    decreasing dt (no sampling). Sampling: simulated correlation against the
    exact discrete-time one for increasing duration at fixed dt; the RMS error
    should fall roughly as duration^-1/2.
    """
    w = np.asarray(scaled, dtype=float)
    off = ~np.eye(len(w), dtype=bool)
    _, exact = linear_fc(w, coupling)
    bias = [
        {
            "dt_tau": dt,
            "max_abs_difference": float(
                np.abs(_correlation(euler_maruyama_covariance(w, coupling, dt)) - exact)[off].max()
            ),
        }
        for dt in (0.2, 0.1, 0.05, 0.025)
    ]
    dt = 0.1
    target = _correlation(euler_maruyama_covariance(w, coupling, dt))
    sampling = []
    for duration in (1000.0, 4000.0, 16000.0):
        samples = simulate_linear(w, coupling, duration=duration, dt=dt, seed=11)
        simulated = np.corrcoef(samples[int(50 / dt) :].T)
        sampling.append(
            {
                "duration_tau": duration,
                "dt_tau": dt,
                "rms_error": float(np.sqrt(np.mean((simulated - target)[off] ** 2))),
            }
        )
    lyapunov = (coupling * w - np.eye(len(w))) @ linear_fc(w, coupling)[0]
    residual = lyapunov + lyapunov.T + np.eye(len(w))
    return {
        "lyapunov_residual_max": float(np.abs(residual).max()),
        "step_bias": bias,
        "sampling": sampling,
        "verification_scope": "analytic/numerical controls, not empirical validation",
    }


def matched_random_integrity(network: PhantomNetwork, integrity: ArrayLike, seed: int = 0):
    """Control lesion: the same multiset of tract integrities assigned to random edges.

    Total structural loss is matched exactly in distribution over edges; only
    which tracts are damaged changes.
    """
    s = np.asarray(integrity, dtype=float)
    iu = np.triu_indices(network.size, 1)
    values = s[iu].copy()
    np.random.default_rng(seed).shuffle(values)
    shuffled = np.ones_like(s)
    shuffled[iu] = values
    shuffled.T[iu] = values
    return shuffled


# Assumed, unsourced mapping from CANTAB measures to phantom regions, for
# illustrating a comparison template only. Planning (SOC) relies on frontal
# regions that this parietal-level coronal slice does not contain.
COGNITIVE_ASSUMPTIONS = {
    "MOT motor latency": ("vertex",),
    "RTI reaction time": ("vertex", "deep"),
    "RVP sustained attention": ("lateral", "superior"),
    "SSP spatial span": ("superior", "medial"),
    "SOC planning": (),
}


def domain_strength(network: PhantomNetwork, weight: ArrayLike) -> dict:
    """Node strength relative to the healthy network, averaged over assumed regions.

    Returns {domain: {"L": value, "R": value}} or None where the domain has no
    region in the phantom. A comparison template, not a cognitive prediction.
    """
    healthy = network.weight.sum(axis=1)
    relative = np.asarray(weight, dtype=float).sum(axis=1) / healthy
    result = {}
    for domain, keys in COGNITIVE_ASSUMPTIONS.items():
        if not keys:
            result[domain] = None
            continue
        result[domain] = {
            side: float(np.mean([relative[network.names.index(f"{side}-{key}")] for key in keys]))
            for side in ("L", "R")
        }
    return result


def lesion_course(
    phantom: CoronalPhantom,
    network: PhantomNetwork,
    run,
    *,
    coupling: float = 0.8,
    spare_callosum: bool = False,
) -> dict:
    """Structural and functional summaries at every snapshot of one growth run."""
    scale = spectral_radius(network.weight)
    healthy = network_summary(network, network.weight)
    _, fc_healthy = linear_fc(network.weight / scale, coupling)
    cross = network.interhemispheric
    rows = {"inter_sc": [], "efficiency": [], "inter_fc": [], "radius": []}
    for density in run.density:
        c = callosum_sparing(phantom, density) if spare_callosum else density
        w = network.weight * tract_integrity(network, c)
        summary = network_summary(network, w)
        _, fc = linear_fc(w / scale, coupling)
        rows["inter_sc"].append(
            summary["interhemispheric_weight"] / healthy["interhemispheric_weight"]
        )
        rows["efficiency"].append(summary["global_efficiency"] / healthy["global_efficiency"])
        rows["inter_fc"].append(float(fc[cross].mean()))
        rows["radius"].append(spectral_radius(w) / scale)
    return {
        "days": run.days.copy(),
        **{key: np.asarray(value) for key, value in rows.items()},
        "healthy_inter_fc": float(fc_healthy[cross].mean()),
        "coupling": float(coupling),
    }


def resection_state(
    phantom: CoronalPhantom,
    network: PhantomNetwork,
    density: ArrayLike,
    *,
    threshold: float = 0.3,
    coupling: float = 0.8,
) -> dict:
    """Healthy, pre-operative and post-operative weights and correlations at one day.

    After resection, residual density outside the cavity still weakens tracts;
    tracts crossing the cavity are cut.
    """
    c = np.asarray(density, dtype=float)
    cavity = resection_cavity(phantom, c, threshold)
    scale = spectral_radius(network.weight)
    weights = {
        "healthy": network.weight,
        "pre-operative": network.weight * tract_integrity(network, c),
        "post-operative": network.weight
        * tract_integrity(network, np.where(cavity, 0.0, c), cavity),
    }
    return {
        "cavity": cavity,
        "cavity_area_mm2": float(cavity.sum() * phantom.spacing_mm**2),
        "threshold": float(threshold),
        "weights": weights,
        "fc": {name: linear_fc(w / scale, coupling)[1] for name, w in weights.items()},
        "summaries": {name: network_summary(network, w) for name, w in weights.items()},
        "domains": {name: domain_strength(network, w) for name, w in weights.items()},
    }
