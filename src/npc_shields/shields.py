from __future__ import annotations

import csv
import functools
import pathlib
from collections.abc import Iterable, Mapping

import pydantic

import npc_shields.types

DRAWINGS_DIR = pathlib.Path(__file__).parent / "drawings"
COORDINATES_DIR = pathlib.Path(__file__).parent / "hole_coordinates"


class Hole(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        frozen=True,
    )

    label: str
    """Label of the hole, as specified in the coords csv & job svg, e.g. 'A1'."""

    target_structure: str | None = None
    """Intended target structure of the hole, e.g. 'VISp', when the corresponding
    probe is inserted, e.g. probe B in B1."""

    location_ap: float | None = None
    """Anterior-posterior distance of the hole, in millimeters, from Bregma
    (positive is anterior)."""

    location_ml: float | None = None
    """Medial-lateral distance of the hole, in millimeters, from midline
    (positive is right hemisphere)."""

    location_z: float | None = None
    """Depth of the hole, in millimeters, origin uncertain."""


@functools.cache
def get_svg_data(
    shield: npc_shields.types.Shield,
) -> str:
    return shield.drawing_svg.read_text()


class Shield(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        frozen=True,
    )

    name: str
    drawing_id: int | str
    drawing_svg: pathlib.Path
    hole_coordinates_csv: pathlib.Path

    def to_json(self) -> dict[str, str | int]:
        return dict(name=self.name, drawing_id=self.drawing_id)

    @property
    def holes(self) -> dict[str, Hole]:
        return get_holes_from_csv(self.hole_coordinates_csv)

    @pydantic.model_validator(mode="after")
    def validate_holes_in_svg(self):
        svg_data = get_svg_data(self)
        for label in self.holes:
            if f">{label}</tspan>" not in svg_data:
                raise ValueError(
                    f"Mismatch between coordinates csv and drawing svg: {label} not found in {self.drawing_svg.name}"
                )


def get_holes_from_csv(csv_path: pathlib.Path) -> dict[str, Hole]:
    """
    >>> holes = get_holes_from_csv(COORDINATES_DIR / "2011.csv")
    >>> holes['B4']
    Hole(label='B4', target_structure='CP coverage', location_ap=0.9, location_ml=-2.2, location_z=None)

    # target structure is empty string if not specified in the csv:
    >>> holes['E2']
    Hole(label='E2', target_structure='', location_ap=-1.3, location_ml=-3.2, location_z=None)
    """
    with open(csv_path, newline="") as csvfile:
        creader = csv.reader(csvfile, delimiter=",")
        columns = creader.__next__()
        # column_dtypes = {'AP': float, 'ML': float, 'Target': str}
        hole_data: dict[str, Hole] = {}
        for row in creader:
            label = row[0]

            def get_column_idx(name) -> int:
                idx = next(
                    (i for i, col in enumerate(columns) if name.lower() in col.lower()),
                    None,
                )
                if idx is None:
                    raise ValueError(
                        f"Column {name!r} not found in csv columns: {columns}"
                    )
                return idx

            try:
                target = row[get_column_idx("Target")]
            except ValueError:
                target = None
            hole_data[label] = Hole(
                label=label,
                target_structure=target or "",
                # pydantic will convert these named params to the correct types:
                location_ap=row[get_column_idx("AP")],  # type: ignore[arg-type]
                location_ml=row[get_column_idx("ML")],  # type: ignore[arg-type]
                # extra columns are will be added as strings:
                **{c: row[get_column_idx(c)] for c in columns[1:] if c not in ("AP", "ML", "Target")},  # type: ignore[arg-type]
            )
    return hole_data


def get_labels_from_mapping(mapping: Mapping[str, Iterable[int]]) -> tuple[str, ...]:
    """Convert a mapping of probe letter to insertion holes to a tuple of labels.

    >>> get_labels_from_mapping({"A": (1, 2, 3), "B": (1, 2, 3, 4)})
    ('A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'B4')
    """
    return tuple(
        f"{letter}{hole}" for letter, holes in mapping.items() for hole in holes
    )


DR2002 = Shield(
    name="2002",
    drawing_id="0283-200-002",
    drawing_svg=DRAWINGS_DIR / "2002.svg",
    hole_coordinates_csv=COORDINATES_DIR / "2002.csv",
)
"""2002 - MPE drawing 0283-200-002"""

TEMPLETON = Shield(
    name="Templeton",  # ? 2001
    drawing_id="0283-200-001",
    drawing_svg=DRAWINGS_DIR / "2001.svg",
    hole_coordinates_csv=COORDINATES_DIR / "2001.csv",
)
"""Templeton implant - MPE drawing 0283-200-001"""

DR2006 = Shield(
    name="2006",
    drawing_id="0283-200-006",
    drawing_svg=DRAWINGS_DIR / "2006.svg",
    hole_coordinates_csv=COORDINATES_DIR / "2006.csv",
)
"""DR2 rev1/2006 - MPE drawing 0283-200-006"""

DR2005 = Shield(
    name="2005",
    drawing_id="0283-200-005",
    drawing_svg=DRAWINGS_DIR / "2005.svg",
    hole_coordinates_csv=COORDINATES_DIR / "2005.csv",
)
"""DR2 rev2/2005 - MPE drawing 0283-200-005"""

DR2011 = Shield(
    name="2011",
    drawing_id="0283-200-11",
    drawing_svg=DRAWINGS_DIR / "2011.svg",
    hole_coordinates_csv=COORDINATES_DIR / "2011.csv",
)
"""DR2011 vis ctx and striatum - MPE drawing 0283-200-11"""

DR2011 = Shield(
    name="2014",
    drawing_id="0283-200-14",
    drawing_svg=DRAWINGS_DIR / "2014.svg",
    hole_coordinates_csv=COORDINATES_DIR / "2014.csv",
)
"""DR2014 dual hemisphere - MPE drawing 0283-200-14"""


def get_svg_data_with_insertions(
    shield: npc_shields.types.Shield,
    insertions: npc_shields.types.InsertionProbeMap,
) -> str:
    data: str = get_svg_data(shield)
    reversed_map = {
        label: sorted(k for k, v in insertions.items() if v == label)
        for label in insertions.values()
        if label is not None
    }
    for label in shield.holes:
        if label not in insertions.values():
            data = data.replace(f">{label}</tspan>", "></tspan>")
        else:
            probe_letters = reversed_map[label]
            data = data.replace(
                f">{label}</tspan>", f"> {''.join(probe_letters)}</tspan>"
            )
    return data


def get_shield(
    name_or_id: str | int,
) -> Shield:
    """
    Get an existing shield instance by name or drawing ID.

    >>> x = get_shield("2002")
    >>> y = get_shield("0283-200-002")
    >>> assert x is y
    """
    for shield in (shields := get_shields()):
        for attr in ("name", "drawing_id"):
            if str(name_or_id).lower() == str(getattr(shield, attr)).lower():
                return shield
    raise ValueError(
        f"Shield {name_or_id!r} not found: should be one of {[s.name for s in shields]}"
    )


def get_shields() -> tuple[Shield, ...]:
    """
    All known shields, sorted by drawing ID.

    >>> x = get_shields()
    """
    return tuple(
        sorted(
            (v for v in globals().values() if isinstance(v, Shield)),
            key=lambda x: x.drawing_id,
        )
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
