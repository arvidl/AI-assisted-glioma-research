"""One patient's brain network before and after glioma surgery, and the linear network model.

The case is sub-PAT16 of the Brain Tumor Connectomics data (Aerts, Marinazzo;
OpenNeuro ds001226 v5.0.0 and ds002080 v4.0.0, CC0). Its 82-region matrices are
derived once from local tractograms by scripts/derive_pat16_connectome.py, which
stays in the archived development repository, and tracked in data/derived/sub-PAT16
with their provenance. The upstream processing
(FreeSurfer, fMRIPrep, QSIPrep, MRtrix3) has not been quality-reviewed; every
result inherits that status. One patient supports description, not inference.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

from glioma_ai.network import linear_fc, spectral_radius

SUBCORTICAL = {
    10: "L-Thalamus",
    11: "L-Caudate",
    12: "L-Putamen",
    13: "L-Pallidum",
    17: "L-Hippocampus",
    18: "L-Amygdala",
    26: "L-Accumbens",
    49: "R-Thalamus",
    50: "R-Caudate",
    51: "R-Putamen",
    52: "R-Pallidum",
    53: "R-Hippocampus",
    54: "R-Amygdala",
    58: "R-Accumbens",
}
# Desikan-Killiany cortical parcels of FreeSurfer aparc+aseg, labels 1001-1035
# (left) and 2001-2035 (right). Label x004 (corpus callosum) is not a parcel.
CORTICAL = (
    "bankssts",
    "caudalanteriorcingulate",
    "caudalmiddlefrontal",
    None,
    "cuneus",
    "entorhinal",
    "fusiform",
    "inferiorparietal",
    "inferiortemporal",
    "isthmuscingulate",
    "lateraloccipital",
    "lateralorbitofrontal",
    "lingual",
    "medialorbitofrontal",
    "middletemporal",
    "parahippocampal",
    "paracentral",
    "parsopercularis",
    "parsorbitalis",
    "parstriangularis",
    "pericalcarine",
    "postcentral",
    "posteriorcingulate",
    "precentral",
    "precuneus",
    "rostralanteriorcingulate",
    "rostralmiddlefrontal",
    "superiorfrontal",
    "superiorparietal",
    "superiortemporal",
    "supramarginal",
    "frontalpole",
    "temporalpole",
    "transversetemporal",
    "insula",
)
CASE_DIR = Path(__file__).resolve().parents[2] / "data/derived/sub-PAT16"
SESSIONS = ("preop", "postop")


def dk82() -> tuple[NDArray[np.int64], tuple[str, ...]]:
    """FreeSurfer labels and names of the 82 regions, in ascending label order.

    This is the order of fc_roi_names.json written by the upstream compute_fc.py.
    """
    table = dict(SUBCORTICAL)
    for k, name in enumerate(CORTICAL):
        if name is not None:
            table[1001 + k] = f"L-{name}"
            table[2001 + k] = f"R-{name}"
    labels = np.array(sorted(table), dtype=np.int64)
    return labels, tuple(table[label] for label in labels)


def node_image(aparc: ArrayLike, labels: ArrayLike) -> NDArray[np.int16]:
    """Relabel a parcellation to 1..n for the given labels; every other voxel becomes 0."""
    volume = np.asarray(aparc).astype(np.int64)
    lookup = np.zeros(max(int(volume.max()), int(np.max(labels))) + 1, dtype=np.int16)
    lookup[np.asarray(labels)] = np.arange(1, len(labels) + 1)
    return lookup[np.clip(volume, 0, None)]


def nearest_label(volume: ArrayLike, radius_mm: float, zooms) -> NDArray:
    """Each voxel's own nonzero label, else the nearest nonzero label within radius_mm.

    Distances are between voxel centres in millimetres; ties go to the first
    offset in a fixed order, so the result is deterministic. Beyond the radius the
    value is 0. This mirrors the radial-search idea of MRtrix3 tck2connectome
    (default 4 mm) at voxel-centre resolution; it is not that implementation.
    """
    v = np.asarray(volume)
    step = np.asarray(zooms[:3], dtype=float)
    reach = np.floor(radius_mm / step).astype(int)
    axes = [np.arange(-r, r + 1) for r in reach]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    distance = np.linalg.norm(grid * step, axis=1)
    keep = distance <= radius_mm
    offsets = grid[keep][np.argsort(distance[keep], kind="stable")]
    padded = np.pad(v, [(r, r) for r in reach])
    out = np.zeros_like(v)
    todo = np.ones(v.shape, dtype=bool)
    for offset in offsets:
        window = tuple(
            slice(r + o, r + o + n) for r, o, n in zip(reach, offset, v.shape, strict=True)
        )
        candidate = padded[window]
        take = todo & (candidate != 0)
        out[take] = candidate[take]
        todo &= ~take
    return out


def voxel_lookup(volume: ArrayLike, affine: ArrayLike, points: ArrayLike, fill=0) -> NDArray:
    """Value of the voxel containing each world point (mm); fill outside or for NaN points."""
    v = np.asarray(volume)
    p = np.asarray(points, dtype=float)
    out = np.full(len(p), fill, dtype=v.dtype)
    finite = np.isfinite(p).all(axis=1)
    inverse = np.linalg.inv(np.asarray(affine, dtype=float))
    index = np.rint(p[finite] @ inverse[:3, :3].T + inverse[:3, 3]).astype(np.int64)
    inside = np.all((index >= 0) & (index < v.shape[:3]), axis=1)
    rows = np.flatnonzero(finite)[inside]
    out[rows] = v[tuple(index[inside].T)]
    return out


def read_tck_header(path: Path) -> tuple[dict, int]:
    """Key-value header of an MRtrix .tck file and the byte offset of its data."""
    header: dict[str, list[str]] = {}
    with Path(path).open("rb") as stream:
        if stream.readline().strip() != b"mrtrix tracks":
            raise ValueError("Not an MRtrix track file.")
        for raw in stream:
            line = raw.decode("latin-1").rstrip("\n")
            if line == "END":
                break
            key, _, value = line.partition(":")
            header.setdefault(key.strip(), []).append(value.strip())
        else:
            raise ValueError("Track header has no END line.")
    if header.get("datatype") != ["Float32LE"]:
        raise ValueError("Only Float32LE track files are supported.")
    offset = int(header["file"][0].split()[1])
    flat = {key: values[0] if len(values) == 1 else values for key, values in header.items()}
    return flat, offset


def streamline_ends(
    path: Path,
    mask: ArrayLike | None = None,
    mask_affine: ArrayLike | None = None,
    chunk_points: int = 1 << 24,
) -> dict:
    """First and last point of every streamline, and whether any point lies in a mask.

    Reads the file through a memory map in chunks that end at streamline
    separators, so arbitrarily large tractograms use bounded memory. Points are
    world coordinates in millimetres as stored in the file.
    """
    header, offset = read_tck_header(path)
    raw = np.memmap(path, dtype="<f4", mode="r", offset=offset)
    data = raw[: len(raw) // 3 * 3].reshape(-1, 3)
    heads, tails, hits = [], [], []
    start, finished = 0, False
    while start < len(data) and not finished:
        block = np.asarray(data[start : start + chunk_points])
        terminator = np.flatnonzero(np.isinf(block[:, 0]))
        if terminator.size:
            block, finished = block[: terminator[0]], True
        separator = np.flatnonzero(np.isnan(block[:, 0]))
        if separator.size == 0:
            if finished and len(block) == 0:
                break
            raise ValueError("A streamline is longer than the chunk; raise chunk_points.")
        block = block[: separator[-1] + 1]
        first = np.r_[0, separator[:-1] + 1]
        last = separator - 1
        if np.any(last < first):
            raise ValueError("Empty streamline in track file.")
        heads.append(block[first])
        tails.append(block[last])
        if mask is not None:
            inside = voxel_lookup(np.asarray(mask, dtype=bool), mask_affine, block, False)
            owner = np.cumsum(np.isnan(block[:, 0])) - np.isnan(block[:, 0])
            hits.append(np.bincount(owner[inside], minlength=len(first)) > 0)
        start += len(block)
    count = sum(len(h) for h in heads)
    if "count" in header and int(header["count"]) != count:
        raise ValueError(f"Header count {header['count']} differs from {count} streamlines read.")
    return {
        "header": header,
        "heads": np.concatenate(heads),
        "tails": np.concatenate(tails),
        "hits": np.concatenate(hits) if mask is not None else None,
    }


def read_weights(path: Path) -> NDArray[np.float64]:
    """Per-streamline weights from a tcksift2 text file (comment lines start with #)."""
    text = "\n".join(
        line for line in Path(path).read_text().splitlines() if not line.startswith("#")
    )
    return np.array(text.split(), dtype=float)


def connectome(a: ArrayLike, b: ArrayLike, weights: ArrayLike, n: int) -> NDArray[np.float64]:
    """Symmetric weight matrix from endpoint nodes 0..n-1; unassigned (-1) and self pairs drop.

    Entry (i, j) sums the weights of streamlines with one end in i and the other
    in j, as tck2connectome -symmetric -zero_diagonal does.
    """
    a, b, w = np.asarray(a), np.asarray(b), np.asarray(weights, dtype=float)
    keep = (a >= 0) & (b >= 0) & (a != b)
    low, high = np.minimum(a[keep], b[keep]), np.maximum(a[keep], b[keep])
    matrix = np.bincount(low * n + high, weights=w[keep], minlength=n * n).reshape(n, n)
    return matrix + matrix.T


@dataclass(frozen=True)
class CaseConnectome:
    """Tracked 82-region matrices of one case.

    sc[session]: SIFT2-weighted streamline sums (arbitrary units) between regions.
    sc_tumour: the part of the pre-operative sums carried by streamlines that
    pass through the pre-operative tumour mask. fc[session]: Pearson correlation
    of cleaned resting-state BOLD (zero diagonal). centroid_mm: pre-operative
    native T1w scanner coordinates (RAS). tumour_fraction: share of each region's
    voxels inside the tumour mask.
    """

    names: tuple[str, ...]
    labels: NDArray[np.int64]
    hemisphere: NDArray[np.str_]
    centroid_mm: NDArray[np.float64]
    tumour_fraction: NDArray[np.float64]
    sc: dict
    sc_tumour: NDArray[np.float64]
    fc: dict
    provenance: dict

    @property
    def size(self) -> int:
        return len(self.names)


def _matrix(path: Path, n: int) -> NDArray[np.float64]:
    m = np.loadtxt(path, delimiter="\t")
    if m.shape != (n, n) or not np.allclose(m, m.T) or np.any(np.diag(m) != 0):
        raise ValueError(f"{path.name} must be a symmetric {n}x{n} matrix with zero diagonal.")
    return m


def load_case(directory: Path = CASE_DIR) -> CaseConnectome:
    directory = Path(directory)
    with (directory / "regions.tsv").open() as stream:
        columns = stream.readline().rstrip("\n").split("\t")
        rows = [dict(zip(columns, line.rstrip("\n").split("\t"), strict=True)) for line in stream]
    labels, names = dk82()
    if tuple(r["name"] for r in rows) != names or [int(r["label"]) for r in rows] != list(labels):
        raise ValueError("regions.tsv does not list the 82 regions in label order.")
    n = len(rows)
    sc = {s: _matrix(directory / f"sc_{s}.tsv", n) for s in SESSIONS}
    tumour = _matrix(directory / "sc_preop_tumour.tsv", n)
    if np.any(tumour > sc["preop"] * (1 + 1e-9) + 1e-9):
        raise ValueError("Tumour-crossing weight exceeds the pre-operative weight.")
    return CaseConnectome(
        names=names,
        labels=labels,
        hemisphere=np.array([r["hemisphere"] for r in rows]),
        centroid_mm=np.array([[float(r[k]) for k in ("x_mm", "y_mm", "z_mm")] for r in rows]),
        tumour_fraction=np.array([float(r["tumour_fraction"]) for r in rows]),
        sc=sc,
        sc_tumour=tumour,
        fc={s: _matrix(directory / f"fc_{s}.tsv", n) for s in SESSIONS},
        provenance=json.loads((directory / "provenance.json").read_text()),
    )


def model_weights(sc: ArrayLike) -> NDArray[np.float64]:
    """log(1 + SIFT2 weight): a stated compression of the heavy-tailed weights, not a fit."""
    w = np.log1p(np.asarray(sc, dtype=float))
    np.fill_diagonal(w, 0.0)
    return w


def upper(matrix: ArrayLike) -> NDArray:
    m = np.asarray(matrix)
    return m[np.triu_indices(len(m), 1)]


def correlation(a: ArrayLike, b: ArrayLike) -> float:
    return float(np.corrcoef(np.ravel(a), np.ravel(b))[0, 1])


def coupling_scan(sc: ArrayLike, fc: ArrayLike, couplings: ArrayLike, scale: float | None = None):
    """Correlation over region pairs between model and measured FC for each coupling g.

    W = log(1 + SC) / scale, with scale the spectral radius of W unless given.
    """
    w = model_weights(sc)
    scale = spectral_radius(w) if scale is None else float(scale)
    measured = upper(fc)
    return np.array([correlation(upper(linear_fc(w / scale, g)[1]), measured) for g in couplings])


def permuted_node_scan(sc: ArrayLike, fc: ArrayLike, coupling: float, count=200, seed=0):
    """Null: the same structural matrix with region labels shuffled before the model."""
    w = model_weights(sc)
    scale = spectral_radius(w)
    measured = upper(fc)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(count):
        order = rng.permutation(len(w))
        _, model = linear_fc(w[np.ix_(order, order)] / scale, coupling)
        values.append(correlation(upper(model), measured))
    return np.array(values)


def virtual_resection(case: CaseConnectome) -> NDArray[np.float64]:
    """Pre-operative weights without every streamline that passes through the tumour mask."""
    return np.clip(case.sc["preop"] - case.sc_tumour, 0.0, None)


def crossing_fraction(case: CaseConnectome) -> NDArray[np.float64]:
    pre = case.sc["preop"]
    return np.divide(case.sc_tumour, pre, out=np.zeros_like(pre), where=pre > 0)


def log_change(before: ArrayLike, after: ArrayLike, pseudo: float = 1.0) -> NDArray[np.float64]:
    """log2((after + p) / (before + p)); p = 1 is about one SIFT2-weighted streamline."""
    return np.log2((np.asarray(after) + pseudo) / (np.asarray(before) + pseudo))


def predicted_fc_change(pre: ArrayLike, post: ArrayLike, coupling: float) -> NDArray[np.float64]:
    """Model FC after minus before, both scaled by the pre-operative spectral radius."""
    w_pre, w_post = model_weights(pre), model_weights(post)
    scale = spectral_radius(w_pre)
    return linear_fc(w_post / scale, coupling)[1] - linear_fc(w_pre / scale, coupling)[1]


def shuffled_resection_null(case: CaseConnectome, coupling: float, count=200, seed=0):
    """Null: the same tumour-crossing fractions assigned to random connected region pairs.

    Returns correlations between predicted and measured FC change, one per shuffle.
    """
    pre = case.sc["preop"]
    measured = upper(case.fc["postop"] - case.fc["preop"])
    iu = np.triu_indices(case.size, 1)
    connected = pre[iu] > 0
    fraction = crossing_fraction(case)[iu][connected]
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(count):
        shuffled = np.zeros_like(pre)
        f = np.zeros(len(iu[0]))
        f[connected] = rng.permutation(fraction)
        shuffled[iu] = f
        shuffled += shuffled.T
        change = predicted_fc_change(pre, pre * (1 - shuffled), coupling)
        values.append(correlation(upper(change), measured))
    return np.array(values)


def homotopic_summary(case: CaseConnectome, coupling: float = 0.8) -> dict:
    """Mean structural weight, measured FC and model FC by kind of region pair, per session.

    Kinds: homotopic (the same region in both hemispheres), other interhemispheric
    and intrahemispheric pairs. Model FC uses each session's own spectral radius.
    """
    index = {name: k for k, name in enumerate(case.names)}
    left = case.hemisphere == "L"
    homotopic = np.zeros((case.size, case.size), dtype=bool)
    for name in case.names:
        if name.startswith("L-"):
            homotopic[index[name], index[f"R-{name[2:]}"]] = True
    upper_half = np.triu(np.ones_like(homotopic), 1)
    across = (np.outer(left, ~left) | np.outer(~left, left)) & upper_half
    kinds = {
        "homotopic": homotopic,
        "other_interhemispheric": across & ~homotopic & ~homotopic.T,
        "intrahemispheric": ~across & upper_half,
    }
    result = {}
    for session in SESSIONS:
        w = model_weights(case.sc[session])
        _, model = linear_fc(w / spectral_radius(w), coupling)
        sc = case.sc[session]
        result[session] = {
            "interhemispheric_weight_percent": 100 * float(sc[across].sum() / sc[upper_half].sum()),
            **{
                kind: {
                    "pairs": int(mask.sum()),
                    "mean_sc": float(sc[mask].mean()),
                    "mean_fc": float(case.fc[session][mask].mean()),
                    "mean_model_fc": float(model[mask].mean()),
                }
                for kind, mask in kinds.items()
            },
        }
    return result


def fisher_standard_error(volumes: int) -> float:
    """1 / sqrt(n - 3): the Fisher-z standard error for independent samples.

    BOLD samples are autocorrelated, so the true sampling error is larger.
    """
    return float(1.0 / np.sqrt(volumes - 3))
