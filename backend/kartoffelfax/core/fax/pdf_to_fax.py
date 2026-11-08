"""Converts one or more dropped documents into a single fax-ready G3 TIFF.

Pipeline: input files (PDF or image) -> merged PDF (pypdf/Pillow) -> Ghostscript
`tiffg3` device at fax resolution (204x98 standard, 204x196 fine). Ghostscript
is a system dependency (`gs` must be on PATH).
"""
from __future__ import annotations

import asyncio
import io
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError

STANDARD_DPI = (204, 98)
FINE_DPI = (204, 196)


class FaxConversionError(RuntimeError):
    """Raised when a document cannot be merged or converted to a fax TIFF."""


def _merge_sync(source_paths: list[Path], output_path: Path) -> None:
    writer = PdfWriter()
    for path in source_paths:
        if not path.is_file():
            raise FaxConversionError(f"Source file not found: {path}")
        try:
            if path.suffix.lower() == ".pdf":
                writer.append(PdfReader(path))
            else:
                with Image.open(path) as img:
                    buf = io.BytesIO()
                    img.convert("RGB").save(buf, format="PDF")
                buf.seek(0)
                writer.append(PdfReader(buf))
        except (PyPdfError, UnidentifiedImageError, OSError) as exc:
            raise FaxConversionError(f"Cannot read {path.name}: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)


async def merge_to_pdf(source_paths: list[Path], output_path: Path) -> Path:
    if not source_paths:
        raise FaxConversionError("No source files given")
    await asyncio.to_thread(_merge_sync, source_paths, output_path)
    return output_path


async def pdf_to_g3_tiff(pdf_path: Path, output_path: Path, fine_resolution: bool = True) -> Path:
    gs = shutil.which("gs")
    if gs is None:
        raise FaxConversionError("Ghostscript (`gs`) is not installed or not on PATH")
    if not pdf_path.is_file():
        raise FaxConversionError(f"PDF not found: {pdf_path}")

    x_dpi, y_dpi = FINE_DPI if fine_resolution else STANDARD_DPI
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        gs,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        "-sDEVICE=tiffg3",
        "-sPAPERSIZE=a4",
        "-dFIXEDMEDIA",
        "-dPDFFitPage",
        f"-r{x_dpi}x{y_dpi}",
        f"-sOutputFile={output_path}",
        str(pdf_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        detail = (stderr or stdout).decode(errors="replace").strip()
        raise FaxConversionError(f"Ghostscript failed (exit {proc.returncode}): {detail}")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise FaxConversionError("Ghostscript produced no output")
    return output_path
