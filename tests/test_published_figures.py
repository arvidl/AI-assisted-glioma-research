"""Integrity and public-source boundaries for publication illustrations."""

import hashlib
import io

import pytest

from glioma_ai import published
from glioma_ai.published import (
    prepare_published_figures,
    prepared_published_figures,
    published_figure_reference,
    verify_published_figure,
)


def test_changed_figure_is_rejected_and_acquisition_requires_explicit_source(tmp_path):
    original = b"known figure bytes"
    expected = hashlib.sha256(original).hexdigest()
    verify_published_figure(original, expected)
    with pytest.raises(ValueError, match="pinned"):
        verify_published_figure(original + b"changed", expected)
    with pytest.raises(ValueError, match="explicit source"):
        prepare_published_figures(tmp_path)
    assert not list(tmp_path.iterdir())


def test_manifest_uses_pinned_public_cases_and_missing_assets_do_not_trigger_download(tmp_path):
    reference = published_figure_reference()
    assert len(reference["revision"]) == 40
    assert reference["license"].startswith("CC BY 4.0")
    assert len(reference["figures"]) == 3
    for entry in reference["figures"]:
        assert "BGO" not in entry["source_path"]
        assert reference["publication_doi"] in entry["source_url"]
        assert entry["name"].endswith(".png")
    assert all(not entry["ready"] for entry in prepared_published_figures(tmp_path))


def fake_release(monkeypatch, payloads: dict[str, bytes]) -> list[str]:
    requested = []

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def urlopen(url, timeout):
        requested.append(url)
        return Response(payloads[url.rsplit("/", 1)[1]])

    monkeypatch.setattr(published.urllib.request, "urlopen", urlopen)
    return requested


def test_fetch_verifies_every_figure_and_keeps_verified_copies(tmp_path, monkeypatch):
    figures = [b"pipeline", b"anatomy", b"hitplot"]
    reference = published_figure_reference()
    reference["figures"] = [
        {**entry, "sha256": hashlib.sha256(data).hexdigest()}
        for entry, data in zip(reference["figures"], figures, strict=True)
    ]
    monkeypatch.setattr(published, "published_figure_reference", lambda: reference)
    names = [entry["name"] for entry in reference["figures"]]
    payloads = dict(zip(names, figures, strict=True))
    requested = fake_release(monkeypatch, payloads)
    result = published.fetch_published_figures(tmp_path / "figures")
    assert result["downloaded"] == 3 and all(
        "/releases/download/published-figures-v1/" in url for url in requested
    )
    assert all(entry["ready"] for entry in prepared_published_figures(tmp_path / "figures"))
    assert published.fetch_published_figures(tmp_path / "figures")["downloaded"] == 0
    payloads[reference["figures"][1]["name"]] = b"substituted"
    with pytest.raises(ValueError, match="pinned"):
        published.fetch_published_figures(tmp_path / "other")
    assert not (tmp_path / "other").exists()
