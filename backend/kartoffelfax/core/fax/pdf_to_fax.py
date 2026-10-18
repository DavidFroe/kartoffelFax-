"""Converts one or more dropped documents into a single fax-ready G3/TIFF stream.

Pipeline: arbitrary input files -> merged PDF (pypdf) -> rasterized pages
(pdf2image/Ghostscript, 204x98 or 204x196 dpi) -> G3 TIFF (via Ghostscript's
tiffg3/tiffg4 device) ready for T.38 transmission.
"""
from __future__ import annotations

from pathlib import Path


async def merge_to_pdf(source_paths: list[Path], output_path: Path) -> Path:
    raise NotImplementedError


async def pdf_to_g3_tiff(pdf_path: Path, output_path: Path, fine_resolution: bool = True) -> Path:
    raise NotImplementedError
