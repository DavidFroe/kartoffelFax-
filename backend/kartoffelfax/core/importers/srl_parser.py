"""Parser for AVM Fritz!fax phonebook exports (.srl files).

NOTE: AVM never published the .srl binary format; it is a legacy, mostly
undocumented structure from the Fritz!fax / T-Online era. This module is a
placeholder until the format has been reverse-engineered against real sample
files (see docs/srl_format_notes.md once that investigation starts). Treat any
parsing logic added here as provisional until validated against multiple
real-world .srl exports.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SrlContact:
    legacy_id: str
    name: str
    fax_number: str | None
    phone_number: str | None


def parse_srl_file(path: Path) -> list[SrlContact]:
    """Parses a .srl phonebook export into a list of contacts.

    Raises NotImplementedError until the binary layout is confirmed.
    """
    raise NotImplementedError(
        "The .srl format needs reverse-engineering against real sample files first"
    )
