"""Handles incoming fax calls: receives G3/TIFF data, converts to PDF + thumbnail,
and inserts a new `fax_messages` row with folder='inbox'.
"""
from __future__ import annotations

from pathlib import Path


async def tiff_to_pdf(tiff_path: Path, output_path: Path) -> Path:
    raise NotImplementedError


async def generate_thumbnail(pdf_path: Path, output_path: Path) -> Path:
    raise NotImplementedError
