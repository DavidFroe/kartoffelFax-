from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from kartoffelfax.core.fax.fax_receiver import generate_thumbnail, tiff_to_pdf
from kartoffelfax.core.fax.pdf_to_fax import FaxConversionError
from PIL import Image, ImageDraw
from pypdf import PdfReader

needs_gs = pytest.mark.skipif(shutil.which("gs") is None, reason="Ghostscript (gs) not installed")


def _make_tiff(path: Path, pages: int = 2, dpi: tuple[int, int] = (204, 196)) -> Path:
    frames = []
    for i in range(pages):
        img = Image.new("1", (1728, 2200), 1)
        ImageDraw.Draw(img).rectangle((100, 100 + i * 50, 900, 400 + i * 50), fill=0)
        frames.append(img)
    frames[0].save(path, save_all=True, append_images=frames[1:], compression="group3", dpi=dpi)
    return path


async def test_tiff_to_pdf_keeps_all_pages(tmp_path: Path) -> None:
    tiff = _make_tiff(tmp_path / "rx.tif", pages=3)

    pdf = await tiff_to_pdf(tiff, tmp_path / "out" / "rx.pdf")

    assert len(PdfReader(pdf).pages) == 3


async def test_tiff_to_pdf_corrects_standard_resolution_aspect(tmp_path: Path) -> None:
    fine = await tiff_to_pdf(_make_tiff(tmp_path / "f.tif", 1, (204, 196)), tmp_path / "f.pdf")
    standard = await tiff_to_pdf(_make_tiff(tmp_path / "s.tif", 1, (204, 98)), tmp_path / "s.pdf")

    def size(p: Path) -> tuple[float, float]:
        box = PdfReader(p).pages[0].mediabox
        return float(box.width), float(box.height)

    fw, fh = size(fine)
    sw, sh = size(standard)
    assert fw == pytest.approx(sw)
    assert sh / fh == pytest.approx(2.0, rel=0.02)


async def test_tiff_to_pdf_rejects_missing_and_corrupt(tmp_path: Path) -> None:
    with pytest.raises(FaxConversionError, match="not found"):
        await tiff_to_pdf(tmp_path / "nope.tif", tmp_path / "x.pdf")
    bad = tmp_path / "bad.tif"
    bad.write_bytes(b"not a tiff")
    with pytest.raises(FaxConversionError, match="bad.tif"):
        await tiff_to_pdf(bad, tmp_path / "x.pdf")


@needs_gs
async def test_generate_thumbnail_is_small_png_of_first_page(tmp_path: Path) -> None:
    pdf = await tiff_to_pdf(_make_tiff(tmp_path / "rx.tif", pages=2), tmp_path / "rx.pdf")

    thumb = await generate_thumbnail(pdf, tmp_path / "thumbs" / "rx.png")

    with Image.open(thumb) as img:
        assert img.format == "PNG"
        assert 0 < img.width < 400
        assert img.height > img.width
        assert img.convert("L").getextrema()[0] < 128


async def test_generate_thumbnail_rejects_missing_pdf(tmp_path: Path) -> None:
    with pytest.raises(FaxConversionError, match="not found"):
        await generate_thumbnail(tmp_path / "nope.pdf", tmp_path / "t.png")
