"""Handles incoming fax calls: receives G3/TIFF data, converts to PDF + thumbnail,
and inserts a new `fax_messages` row with folder='inbox'.

Uses the same toolchain as pdf_to_fax (Pillow for TIFF, Ghostscript for rendering).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from PIL import Image, ImageSequence, UnidentifiedImageError

from kartoffelfax.core.fax.pdf_to_fax import FaxConversionError, run_ghostscript

_THUMBNAIL_DPI = 36


def _tiff_to_pdf_sync(tiff_path: Path, output_path: Path) -> None:
    try:
        with Image.open(tiff_path) as tiff:
            x_dpi, y_dpi = (float(v) for v in tiff.info.get("dpi", (204, 196)))
            pages = []
            for frame in ImageSequence.Iterator(tiff):
                gray = frame.convert("L")
                if abs(x_dpi - y_dpi) > 1:
                    # Fax "standard" mode has non-square pixels; PDF export assumes square ones.
                    gray = gray.resize((gray.width, round(gray.height * x_dpi / y_dpi)), Image.LANCZOS)
                pages.append(gray)
    except (UnidentifiedImageError, OSError) as exc:
        raise FaxConversionError(f"Cannot read TIFF {tiff_path.name}: {exc}") from exc

    if not pages:
        raise FaxConversionError(f"TIFF {tiff_path.name} contains no pages")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(output_path, "PDF", save_all=True, append_images=pages[1:], resolution=x_dpi)


async def tiff_to_pdf(tiff_path: Path, output_path: Path) -> Path:
    if not tiff_path.is_file():
        raise FaxConversionError(f"TIFF not found: {tiff_path}")
    await asyncio.to_thread(_tiff_to_pdf_sync, tiff_path, output_path)
    return output_path


async def generate_thumbnail(pdf_path: Path, output_path: Path) -> Path:
    if not pdf_path.is_file():
        raise FaxConversionError(f"PDF not found: {pdf_path}")
    return await run_ghostscript(
        "-sDEVICE=png16m",
        "-dFirstPage=1",
        "-dLastPage=1",
        "-dTextAlphaBits=4",
        "-dGraphicsAlphaBits=4",
        f"-r{_THUMBNAIL_DPI}",
        input_path=pdf_path,
        output_path=output_path,
    )
