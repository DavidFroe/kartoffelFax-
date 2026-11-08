from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from kartoffelfax.core.fax.pdf_to_fax import FaxConversionError, merge_to_pdf, pdf_to_g3_tiff
from PIL import Image
from pypdf import PdfReader, PdfWriter

needs_gs = pytest.mark.skipif(shutil.which("gs") is None, reason="Ghostscript (gs) not installed")


def _make_pdf(path: Path, pages: int = 1) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


def _make_png(path: Path) -> Path:
    Image.new("RGB", (200, 300), "black").save(path)
    return path


async def test_merge_combines_pdfs_and_images(tmp_path: Path) -> None:
    a = _make_pdf(tmp_path / "a.pdf", pages=2)
    b = _make_pdf(tmp_path / "b.pdf", pages=1)
    img = _make_png(tmp_path / "c.png")

    out = await merge_to_pdf([a, b, img], tmp_path / "out" / "merged.pdf")

    assert len(PdfReader(out).pages) == 4


async def test_merge_rejects_missing_and_empty(tmp_path: Path) -> None:
    with pytest.raises(FaxConversionError):
        await merge_to_pdf([], tmp_path / "x.pdf")
    with pytest.raises(FaxConversionError, match="not found"):
        await merge_to_pdf([tmp_path / "nope.pdf"], tmp_path / "x.pdf")


async def test_merge_rejects_corrupt_input(tmp_path: Path) -> None:
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(FaxConversionError, match="bad.png"):
        await merge_to_pdf([bad], tmp_path / "x.pdf")


@needs_gs
@pytest.mark.parametrize(("fine", "dpi"), [(True, (204, 196)), (False, (204, 98))])
async def test_pdf_to_g3_tiff_resolution(tmp_path: Path, fine: bool, dpi: tuple[int, int]) -> None:
    pdf = _make_pdf(tmp_path / "in.pdf", pages=2)

    tiff = await pdf_to_g3_tiff(pdf, tmp_path / "out.tif", fine_resolution=fine)

    assert tiff.stat().st_size > 0
    assert tiff.read_bytes()[:4] in (b"II*\x00", b"MM\x00*")
    with Image.open(tiff) as img:
        assert img.format == "TIFF"
        assert img.n_frames == 2
        assert img.info["compression"] == "group3"
        assert tuple(round(v) for v in img.info["dpi"]) == dpi


@needs_gs
async def test_pdf_to_g3_tiff_fails_on_invalid_pdf(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"garbage")
    with pytest.raises(FaxConversionError):
        await pdf_to_g3_tiff(bad, tmp_path / "out.tif")


async def test_pdf_to_g3_tiff_reports_missing_ghostscript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    with pytest.raises(FaxConversionError, match="Ghostscript"):
        await pdf_to_g3_tiff(_make_pdf(tmp_path / "in.pdf"), tmp_path / "out.tif")
