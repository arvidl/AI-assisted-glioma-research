"""3D Patient-048 adapter on a synthetic prepared grid: tissue tables, components, scoring."""

import json

import nibabel as nib
import numpy as np
import pytest

from glioma_ai import lumiere_volume as lv
from glioma_ai.lumiere_slice import LABEL_SCHEME

SHAPE = (30, 30, 30)


def _ball(radius: float, centre=(15, 15, 15)) -> np.ndarray:
    grid = np.indices(SHAPE).astype(float)
    return sum((g - c) ** 2 for g, c in zip(grid, centre, strict=True)) <= radius**2


def _save(array, path, *, units=True):
    image = nib.Nifti1Image(array, np.eye(4))
    if units:
        image.header.set_xyzt_units("mm")
    nib.save(image, path)


def prepared_volume(tmp_path, *, with_tissue=True):
    labels = {
        "week-045": np.where(_ball(3), 4, np.where(_ball(5), 2, 0)),
        "week-049": np.where(_ball(4), 4, np.where(_ball(7) | _ball(2, (4, 4, 25)), 2, 0)),
    }
    for visit, values in labels.items():
        base = tmp_path / "derivatives" / f"tp-{visit}"
        (base / "seg_dl").mkdir(parents=True)
        _save(
            np.where(_ball(13), 100.0, 0.0).astype(np.float32),
            base / f"tp-{visit}_CT1_to_ref.nii.gz",
        )
        _save(
            values.astype(np.uint8),
            base / "seg_dl" / f"tp-{visit}_seg_brats3_dl.nii.gz",
            units=False,
        )
        (base / "seg_dl" / f"tp-{visit}_seg_brats3_dl.json").write_text(
            json.dumps(
                {
                    "backend": "monai_bundle",
                    "bundle_version": "0.4.8",
                    "label_scheme": LABEL_SCHEME,
                    "voxel_spacing_mm": [1, 1, 1],
                }
            )
        )
    if with_tissue:
        wmparc = np.zeros(SHAPE, dtype=np.int32)
        wmparc[_ball(13)] = 5001
        wmparc[_ball(13) & (np.indices(SHAPE)[0] < 12)] = 1024
        wmparc[_ball(13) & (np.indices(SHAPE)[0] == 22)] = 24
        folder = tmp_path / "derivatives" / "tp-week-045" / "parcellation"
        folder.mkdir()
        _save(wmparc, folder / "tp-week-045_wmparc_native.nii.gz", units=False)
    return tmp_path


def test_tissue_tables_group_freesurfer_labels_and_report_the_rest():
    tissue, record = lv.tissue_classes(np.array([0, 4, 24, 3, 1024, 2035, 2, 4012, 5002, 30]))
    assert tissue.tolist() == [0, 1, 1, 2, 2, 2, 3, 3, 3, 0]
    assert record["unclassified_labels"] == [30]


def test_components_are_face_connected():
    mask = np.zeros((5, 5, 5), dtype=bool)
    mask[1, 1, 1] = mask[2, 2, 2] = True
    mask[3, 3, 3] = mask[3, 3, 4] = True
    labels = lv.component_labels_3d(mask)
    assert len(np.unique(labels[mask])) == 3
    assert labels[3, 3, 3] == labels[3, 3, 4]


def test_case_crops_from_week_045_and_splits_on_the_full_volume(tmp_path):
    case = lv.load_volume_case(prepared_volume(tmp_path), margin_mm=4)
    observed = case.metadata["observed"]
    assert case.metadata["crop_shape"] == [19, 19, 19]
    assert observed["n_later_components"] == 2 and observed["n_local_components"] == 1
    assert observed["local_whole_cm3"] == pytest.approx(_ball(7).sum() / 1000)
    assert observed["distant_whole_cm3"] == pytest.approx(_ball(2, (4, 4, 25)).sum() / 1000)
    assert case.split["distant_in_crop"].sum() == 0
    assert (
        "derivatives/tp-week-045/parcellation/tp-week-045_wmparc_native.nii.gz"
        in (case.metadata["source_sha256"])
    )


def test_tissue_weighting_keeps_the_domain_mean_and_the_five_to_one_ratio(tmp_path):
    case = lv.load_volume_case(prepared_volume(tmp_path), margin_mm=4)
    domain = lv.growth_domain(case, "parenchyma")
    field, record = lv.tissue_diffusivity(case, 0.08, domain)
    assert field[domain].mean() == pytest.approx(0.08)
    assert record["d_white_mm2_per_day"] == pytest.approx(5 * record["d_grey_mm2_per_day"])
    unlabelled_csf = (case.tissue == lv.CSF) & ~case.roi("week-045", (1, 2, 4))
    assert unlabelled_csf.any() and not (domain & unlabelled_csf).any()


def test_runs_score_against_full_volume_counts_and_keep_the_crop_quiet(tmp_path):
    case = lv.load_volume_case(prepared_volume(tmp_path), margin_mm=6)
    runs = lv.compare_volume_variants(
        case, fit={"diffusivity_mm2_per_day": 0.25, "rho_per_day": 0.1}
    )
    assert len(runs) == 5
    for result in runs.values():
        assert 0 <= result["model"]["local_score"] <= 1
        assert result["max_balance_residual_mm3"] < 1e-8
        assert result["days"][-1] == lv.INTERVAL_DAYS
    fit = runs["2D fit, brain support"]["model"]
    assert fit["whole_cm3"] > runs["Literature, brain support"]["model"]["whole_cm3"]


def test_without_tissue_only_the_brain_support_runs(tmp_path):
    case = lv.load_volume_case(prepared_volume(tmp_path, with_tissue=False), margin_mm=4)
    assert case.tissue is None
    assert list(lv.compare_volume_variants(case)) == ["Literature, brain support"]
    with pytest.raises(ValueError, match="wmparc"):
        lv.growth_domain(case, "parenchyma")
