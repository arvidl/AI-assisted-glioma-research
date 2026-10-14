import json
import math
import re

import numpy as np
import pytest

from glioma_ai import btc_cantab
from glioma_ai.btc_cantab import (
    GROUP_OF_LABEL,
    MEASURES,
    audit_reported,
    bootstrap_indices,
    case_change_table,
    case_scores,
    change_indices,
    cohort_counts,
    cross_source_agreement,
    forecast_table,
    group_summary,
    leave_one_out,
    load_cohort,
    percent_improvement,
    read_table,
    reading,
    retest_statistics,
)
from glioma_ai.cantab import reliable_change_index

HEADER = ["participant_id", " sex", "tumor type & grade", "tumor size (cub cm)", "tumor location"]


def _row(identifier, label, scores, size="0"):
    return [identifier, "M", label, size, "none" if label == "none" else "Frontal", *scores]


def _write(path, rows):
    lines = ["\t".join(HEADER + list(MEASURES))]
    lines += ["\t".join(str(v) for v in row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _scores(shift=0.0, span=5):
    return [700 + shift, 350 + shift, 360 + shift, 0.9, 8, span]


@pytest.fixture
def cohort_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(btc_cantab, "verify_btc", lambda directory: {})
    rng = np.random.default_rng(1)
    pre, post = [], []
    for i in range(6):
        base = rng.normal(0, 30)
        pre.append(_row(f"sub-CON{i:02d}", "none", _scores(base, 5 + i % 2)))
        post.append(_row(f"sub-CON{i:02d}", "none", _scores(base + rng.normal(5, 10), 5 + i % 3)))
    pre.append(_row("sub-PAT01", "Meningioma I", _scores(40), "12.5"))
    post.append(_row("sub-PAT01", "Meningioma I", _scores(30)))
    pre.append(_row("sub-PAT16", "Anaplastic astrocytoma II-III", _scores(60, 6), "50.24"))
    post.append(_row("sub-PAT16", "Anaplastic astrocytoma II-III", _scores(10, 7)))
    pre.append(_row("sub-PAT02", "Oligodendroglioma II", ["n/a"] * len(MEASURES)))
    _write(tmp_path / "ds001226_participants.tsv", pre)
    _write(tmp_path / "ds002080_participants.tsv", post)
    return tmp_path


def test_reference_pins_versions_hashes_and_licence():
    reference = btc_cantab.btc_reference()
    assert reference["license"].startswith("CC0") and reference["data_in_git"] is False
    assert set(reference["files"]) == {
        "ds001226_participants.tsv",
        "ds002080_participants.tsv",
        "sub-PAT16_sessions.tsv",
        "sub-PAT16_sessions.json",
    }
    for spec in reference["files"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", spec["sha256"])
        assert spec["download_url"].startswith("https://raw.githubusercontent.com/")
        assert spec["version"] in spec["download_url"] and spec["size_bytes"] > 0
    for name in ("ds001226_participants.tsv", "ds002080_participants.tsv"):
        spec = reference["files"][name]
        assert spec["doi"] == f"10.18112/openneuro.{spec['dataset']}.v{spec['version']}"


def test_label_map_and_measures_are_explicit():
    assert set(GROUP_OF_LABEL.values()) == {"CON", "MEN", "GLI"}
    assert GROUP_OF_LABEL["Ependymoma II"] == "GLI"
    for spec in MEASURES.values():
        assert spec["sense"] in (-1, 1) and spec["unit"]


def test_read_table_strips_header_spaces_and_rejects_duplicates(tmp_path):
    path = tmp_path / "t.tsv"
    path.write_text("participant_id\t sex\nsub-A\tF\n")
    assert read_table(path)["sub-A"]["sex"] == "F"
    path.write_text("participant_id\tsex\nsub-A\tF\nsub-A\tM\n")
    with pytest.raises(ValueError, match="unique"):
        read_table(path)


def test_load_cohort_groups_counts_and_case(cohort_dir):
    cohort = load_cohort(cohort_dir)
    counts = cohort_counts(cohort)
    assert counts["CON"]["baseline_rows"] == 6 and counts["CON"]["pairs"]["RVP_A"] == 6
    assert counts["GLI"] == {
        "baseline_rows": 2,
        "baseline_with_cantab": 1,
        "followup_rows": 1,
        "pairs": dict.fromkeys(MEASURES, 1),
    }
    case = case_scores(cohort)
    assert case["scores"]["SSP_spanlength"] == (6.0, 7.0)
    assert case["size_cm3"] == 50.24 and case["group"] == "GLI"
    summary = group_summary(cohort, "SSP_spanlength")
    assert {(r["group"], r["session"]) for r in summary} >= {("CON", "preop"), ("GLI", "postop")}
    assert all(r["q1"] <= r["median"] <= r["q3"] for r in summary)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"label": "Glioblastoma IV"}, "Unknown tumour label"),
        ({"span": "12"}, "outside its scale"),
        ({"span": "5.5"}, "whole count"),
    ],
)
def test_load_cohort_refuses_unknown_labels_and_impossible_scores(cohort_dir, change, message):
    path = cohort_dir / "ds001226_participants.tsv"
    rows = [line.split("\t") for line in path.read_text().splitlines()]
    if "label" in change:
        rows[1][2] = change["label"]
    else:
        rows[1][-1] = change["span"]
    path.write_text("\n".join("\t".join(r) for r in rows) + "\n")
    with pytest.raises(ValueError, match=message):
        load_cohort(cohort_dir)


def test_follow_up_without_baseline_and_label_change_are_refused(cohort_dir):
    path = cohort_dir / "ds002080_participants.tsv"
    text = path.read_text()
    path.write_text(text.replace("sub-PAT01", "sub-PAT99"))
    with pytest.raises(ValueError, match="lacks a baseline"):
        load_cohort(cohort_dir)
    path.write_text(text.replace("Meningioma I", "Meningioma II"))
    with pytest.raises(ValueError, match="differs between sessions"):
        load_cohort(cohort_dir)


def test_retest_statistics_match_their_definitions():
    x = np.array([5.0, 6, 7, 8, 9, 6])
    y = np.array([6.0, 6, 8, 8, 10, 7])
    stats = retest_statistics(x, y)
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (intercept + slope * x)
    assert stats["r"] == pytest.approx(np.corrcoef(x, y)[0, 1])
    assert stats["practice"] == pytest.approx((y - x).mean())
    assert stats["slope"] == pytest.approx(slope) and stats["intercept"] == pytest.approx(intercept)
    assert stats["see"] == pytest.approx(math.sqrt((residual**2).sum() / (x.size - 2)))
    assert retest_statistics(np.ones(4), np.arange(4.0)) is None
    with pytest.raises(ValueError):
        retest_statistics(x[:2], y[:2])


def test_change_indices_reduce_to_jacobson_truax_and_known_values():
    stats = {
        "sd_baseline": 1.2,
        "r": 0.6,
        "practice": 0.5,
        "intercept": 1.0,
        "slope": 0.8,
        "see": 0.9,
    }
    result = change_indices(5.0, 6.0, stats)
    classic = reliable_change_index(5.0, 6.0, 1.2, 0.6)
    assert result["jacobson_truax"] == pytest.approx(classic["rci"])
    assert result["practice_adjusted"] == pytest.approx(0.5 / classic["s_diff"])
    assert result["regression_based"] == pytest.approx((6.0 - (1.0 + 0.8 * 5.0)) / 0.9)


def test_reading_uses_direction_and_threshold():
    assert reading(2.5, 1) == "reliable improvement"
    assert reading(2.5, -1) == "reliable decline"
    assert reading(-1.0, 1) == "within the reference variation"


def test_bootstrap_is_seeded_and_ordered():
    rng = np.random.default_rng(3)
    x = rng.normal(10, 2, 10)
    y = x + rng.normal(0.5, 1, 10)
    first = bootstrap_indices(x, y, 10.0, 13.0, n_boot=300)
    second = bootstrap_indices(x, y, 10.0, 13.0, n_boot=300)
    assert first == second
    for low, high in first["intervals"].values():
        assert low <= high


def test_case_change_table_and_leave_out(cohort_dir):
    cohort = load_cohort(cohort_dir)
    table = case_change_table(cohort, n_boot=200)
    row = next(r for r in table if r["measure"] == "SSP_spanlength")
    assert row["defined"] and row["reference"]["n"] == 6
    left_out = case_change_table(cohort, exclude=("sub-CON00",), n_boot=200)
    assert next(r for r in left_out if r["measure"] == "MOT_latency_mean")["reference"]["n"] == 5


def test_leave_one_out_recovers_exact_rules():
    x = np.array([3.0, 5, 6, 8, 9])
    assert leave_one_out(x, x)["persistence"] == 0
    assert leave_one_out(x, x + 2)["mean_change"] == pytest.approx(0)
    assert leave_one_out(x, 2 * x + 1)["regression"] == pytest.approx(0)


def test_forecast_table_pools_groups(cohort_dir):
    cohort = load_cohort(cohort_dir)
    rows = {r["measure"]: r for r in forecast_table(cohort, groups=("CON",))}
    x, y = btc_cantab.paired_values(cohort, "SSP_spanlength", "CON")
    assert rows["SSP_spanlength"] == {"measure": "SSP_spanlength", "unit": "span (2 to 9)"} | (
        leave_one_out(x, y)
    )
    assert forecast_table(cohort)[0]["n"] == 8


def test_column_audit_separates_medians_from_means():
    rng = np.random.default_rng(5)
    cohort = []
    for i in range(12):
        trials = rng.integers(250, 500, 8)
        row = {
            "RTI_fiveRT": str(float(np.median(trials))),
            "RTI_fiveMT": f"{trials.mean() + 0.013:.4f}",
            "RTI_fiveMT_mean": f"{rng.normal(450, 40):.3f}",
            "RTI_fiveMT_md": "n/a" if i == 0 else str(430 + i),
        }
        cohort.append({"raw": {"preop": row, "postop": None}})
    audit = btc_cantab.column_audit(cohort)
    assert audit["n"] == 11
    assert audit["columns"]["RTI_fiveRT"]["half_ms_grid"] == 1.0
    assert audit["columns"]["RTI_fiveMT"]["half_ms_grid"] == 0.0
    assert audit["correlation"]["RTI_fiveRT"]["RTI_fiveMT"] > 0.8
    assert btc_cantab.on_grid(np.array([1.0, 1.5, 1.25])) == pytest.approx(2 / 3)


def test_markdown_table_and_osf_crosswalk():
    assert btc_cantab.markdown_table(["a", "b"], [[1, 2]]) == "| a | b |\n| --- | --- |\n| 1 | 2 |"
    assert btc_cantab.OSF_ID[btc_cantab.CASE] == "PAT16"


def test_cross_source_agreement_uses_released_precision():
    case = {
        "text": {code: ("0.95", "0.9523") if code == "RVP_A" else ("6", "7") for code in MEASURES}
    }
    twin = {
        session: {spec["twin"]: case["text"][code][i] for code, spec in MEASURES.items()}
        for i, session in enumerate(("ses-preop", "ses-postop"))
    }
    osf = {
        f"{spec['osf']}_t{t}": "0.95" if code == "RVP_A" else ("6", "7")[t - 1]
        for code, spec in MEASURES.items()
        if spec["osf"]
        for t in (1, 2)
    }
    rows = cross_source_agreement(case, twin, osf)
    rvp = [r for r in rows if r["measure"] == "RVP_A"]
    assert [r["twin_agreement"] for r in rvp] == ["exact", "exact"]
    assert [r["osf_agreement"] for r in rvp] == ["exact", "at_release_precision"]
    assert all(r["osf"] is None for r in rows if r["measure"] == "RTI_simpleRT_mean")


def test_audit_flags_impossible_values_and_inconsistent_percentages():
    case = {"scores": {"RVP_A": (0.95, 0.95), "MOT_latency_mean": (817.8, 844.5)}}
    reported = {
        "RVP_A": {"values": (158, 140), "percent": -6.5},
        "MOT_latency_mean": {"values": (810, 830), "percent": -2.5},
    }
    rows = {r["measure"]: r for r in audit_reported(reported, case)}
    assert rows["RVP_A"]["within_scale"] is False
    assert rows["MOT_latency_mean"]["within_scale"] is True
    assert rows["MOT_latency_mean"]["percent_from_reported_values"] == pytest.approx(-2.469, 1e-3)
    assert rows["MOT_latency_mean"]["percent_from_source"] == pytest.approx(-3.265, 1e-3)
    assert percent_improvement(400, 340, -1) == pytest.approx(15.0)


def test_change_summary_orients_indices_and_requires_all_three():
    def row(sense, values, share=0.5):
        return {
            "defined": True,
            "measure": "RTI_fiveRT",
            "sense": sense,
            "baseline": 400.0,
            "follow_up": 360.0,
            "reference": {"n": 10},
            "bootstrap": {"share_beyond_threshold": dict.fromkeys(btc_cantab.INDICES, share)},
            **dict(zip(btc_cantab.INDICES, values, strict=True)),
        }

    rows = btc_cantab.change_summary(
        [row(-1, (-2.5, -3.0, -2.1)), row(-1, (-0.8, -1.94, -0.9)), row(1, (2.5, 1.0, 3.0))]
        + [{"defined": False}]
    )
    assert len(rows) == 3 and rows[0]["percent"] == pytest.approx(10.0)
    assert rows[0]["verdict"] == "reliable improvement on all three indices"
    assert rows[1]["oriented"]["practice_adjusted"] == pytest.approx(1.94)
    assert rows[1]["largest"] == "practice_adjusted"
    assert rows[1]["verdict"].startswith("within")
    assert rows[2]["verdict"] == "beyond ±1.96 on 2 of 3 indices only"


def test_existing_file_that_differs_is_preserved(tmp_path):
    (tmp_path / "ds001226_participants.tsv").write_text("changed\n")
    with pytest.raises(ValueError, match="preserve it"):
        btc_cantab.fetch_btc(tmp_path)
    assert (tmp_path / "ds001226_participants.tsv").read_text() == "changed\n"


def test_reference_json_is_valid_json():
    json.loads(btc_cantab.REFERENCE.read_text())


def test_figures_draw_from_group_summaries(cohort_dir):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from glioma_ai.btc_cantab_figures import (
        change_scenario,
        draw_case,
        draw_change_forest,
        draw_change_scenario,
        draw_cohort,
        draw_infographic,
    )

    cohort = load_cohort(cohort_dir)
    table = case_change_table(cohort, n_boot=100)
    figure = plt.figure()
    draw_infographic(figure, cohort, table)
    raw, change = figure.axes
    assert len(raw.get_yticklabels()) == len(btc_cantab.change_summary(table))
    texts = [t.get_text() for t in figure.texts]
    overall = texts[texts.index("Overall:") + 1]
    assert overall.startswith(("No measure changed reliably", "Reliable change in"))
    plt.close(figure)
    for draw, argument in (
        (draw_case, cohort),
        (draw_cohort, cohort),
        (draw_change_forest, case_change_table(cohort, n_boot=100)),
        (draw_change_scenario, change_scenario(cohort, "RTI_fiveRT", True, n_boot=100)),
    ):
        figure = plt.figure()
        draw(figure, argument)
        assert figure.axes
        plt.close(figure)
