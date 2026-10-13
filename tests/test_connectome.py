import json

import nibabel as nib
import numpy as np
import pytest

from glioma_ai.connectome import (
    CASE_DIR,
    connectome,
    dk82,
    load_case,
    nearest_label,
    node_image,
    predicted_fc_change,
    read_weights,
    shuffled_resection_null,
    streamline_ends,
    virtual_resection,
    voxel_lookup,
)
from glioma_ai.provenance import sha256

needs_case = pytest.mark.skipif(
    not CASE_DIR.is_dir(), reason="tracked sub-PAT16 matrices absent (staged public snapshot)"
)


def test_region_table_matches_upstream_order():
    labels, names = dk82()
    assert len(labels) == 82 and list(labels) == sorted(labels)
    assert names[:2] == ("L-Thalamus", "L-Caudate") and names[14] == "L-bankssts"
    assert 1004 not in labels and 2004 not in labels
    assert names[-1] == "R-insula" and labels[-1] == 2035


def test_node_image_and_nearest_label_radius():
    volume = np.zeros((9, 9, 9), dtype=np.int16)
    volume[4, 4, 4] = 1035
    volume[0, 0, 0] = 10
    nodes = node_image(volume, [10, 1035])
    assert nodes[4, 4, 4] == 2 and nodes[0, 0, 0] == 1 and nodes.sum() == 3
    search = nearest_label(nodes, 2.0, (1.0, 1.0, 1.0))
    assert search[4, 4, 6] == 2 and search[4, 4, 7] == 0
    assert search[5, 5, 4] == 2 and search[6, 6, 4] == 0
    assert search[1, 1, 0] == 1 and search[4, 4, 4] == 2


def test_voxel_lookup_handles_outside_and_nan():
    volume = np.arange(27).reshape(3, 3, 3)
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    points = np.array([[2.0, 0.0, 4.0], [100.0, 0.0, 0.0], [np.nan, 0.0, 0.0]])
    assert list(voxel_lookup(volume, affine, points, fill=-1)) == [11, -1, -1]


def write_tck(path, streamlines):
    tractogram = nib.streamlines.Tractogram(streamlines, affine_to_rasmm=np.eye(4))
    nib.streamlines.save(tractogram, str(path))


def test_tck_reader_matches_nibabel_across_chunks(tmp_path):
    rng = np.random.default_rng(3)
    lines = [rng.normal(size=(int(n), 3)).astype(np.float32) * 5 for n in rng.integers(2, 30, 40)]
    lines[5][3] = [0.2, 0.1, -0.3]
    path = tmp_path / "small.tck"
    write_tck(path, lines)
    mask = np.zeros((3, 3, 3), dtype=bool)
    mask[1, 1, 1] = True
    affine = np.eye(4)
    affine[:3, 3] = -1.0
    ends = streamline_ends(path, mask, affine, chunk_points=64)
    assert np.allclose(ends["heads"], [s[0] for s in lines])
    assert np.allclose(ends["tails"], [s[-1] for s in lines])
    expected = [bool(voxel_lookup(mask, affine, s, False).any()) for s in lines]
    assert list(ends["hits"]) == expected and ends["hits"][5]
    with pytest.raises(ValueError, match="longer than the chunk"):
        streamline_ends(path, chunk_points=8)


def test_connectome_is_symmetric_and_drops_unassigned_and_self():
    a = np.array([0, 1, 2, -1, 1])
    b = np.array([1, 0, 2, 1, 2])
    matrix = connectome(a, b, np.array([1.0, 2.0, 5.0, 7.0, 0.5]), 3)
    assert matrix[0, 1] == matrix[1, 0] == 3.0
    assert matrix[1, 2] == 0.5 and np.all(np.diag(matrix) == 0)
    assert matrix.sum() == 2 * 3.5


def test_read_weights_skips_comments(tmp_path):
    path = tmp_path / "w.txt"
    path.write_text("# command_history: tcksift2 a b c\n0.5 1.25 2e-1\n")
    assert np.allclose(read_weights(path), [0.5, 1.25, 0.2])


@needs_case
def test_tracked_case_is_consistent_and_free_of_local_paths():
    case = load_case()
    record = case.provenance
    for name, digest in record["files"].items():
        assert sha256(CASE_DIR / name) == digest
    text = json.dumps(record)
    assert "/Users/" not in text and "/home/" not in text
    assert record["upstream_qc"]["items_total"] > 0
    assert record["license"].startswith("CC0")
    assert np.all(case.sc_tumour <= case.sc["preop"] + 1e-6)
    assert np.all(np.abs(case.fc["preop"]) <= 1)
    for session in ("preop", "postop"):
        check = record["sessions"][session].get("upstream_all_label_check")
        if check:
            assert check["edge_correlation"] > 0.99


@needs_case
def test_virtual_resection_and_nulls():
    case = load_case()
    virtual = virtual_resection(case)
    assert np.all(virtual <= case.sc["preop"]) and np.all(virtual >= 0)
    pre = case.sc["preop"]
    assert np.allclose(predicted_fc_change(pre, pre, 0.8), 0.0)
    first = shuffled_resection_null(case, 0.8, count=3, seed=1)
    assert np.allclose(first, shuffled_resection_null(case, 0.8, count=3, seed=1))
