from __future__ import annotations

import dataclasses
import functools
import pathlib
from collections.abc import Iterable, Mapping

import npc_shields.types

DRAWINGS_DIR = pathlib.Path(__file__).parent / "drawings"


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Shield:
    name: str
    drawing_id: int | str
    labels: Iterable[str] = dataclasses.field(repr=False)
    svg: pathlib.Path


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
    labels=get_labels_from_mapping(
        {
            "A": (1, 2, 3),
            "B": (1, 2, 3, 4),
            "C": (1, 2, 3, 4),
            "D": (1, 2, 3),
            "E": (1, 2, 3, 4),
            "F": (1, 2, 3),
        }
    ),
    svg=DRAWINGS_DIR / "2002.svg",
)
"""TS5/2002 - MPE drawing 0283-200-002"""

TEMPLETON = Shield(
    name="Templeton",  # ? 2001
    drawing_id="0283-200-001",
    labels=get_labels_from_mapping(
        {
            "A": (1, 2, 3),
            "B": (1, 2, 3),
            "C": (1, 2, 3, 4),
            "D": (1,),
            "E": (),
            "F": (1, 2),
        }
    ),
    svg=DRAWINGS_DIR / "2001.svg",
)
"""Templeton implant - MPE drawing 0283-200-001"""

DR2006 = Shield(
    name="2006",
    drawing_id="0283-200-006",
    labels=get_labels_from_mapping(
        {
            "A": (1, 2),
            "B": (1, 2, 3),
            "C": (1, 2, 3),
            "D": (1,),
            "E": (1, 2, 3),
            "F": (1, 2),
        }
    ),
    svg=DRAWINGS_DIR / "2006.svg",
)
"""DR2 rev1/2006 - MPE drawing 0283-200-006"""

DR2005 = Shield(
    name="2005",
    drawing_id="0283-200-005",
    labels=get_labels_from_mapping(
        {
            "A": (1, 2, 3, 4),
            "B": (1, 2, 3),
            "C": (1, 2),
            "D": (1,),
            "E": (1, 2, 3),
            "F": (1, 2),
        }
    ),
    svg=DRAWINGS_DIR / "2005.svg",
)
"""DR2 rev2/2005 - MPE drawing 0283-200-005"""


@functools.cache
def get_svg_data(
    shield: npc_shields.types.Shield,
) -> str:
    return shield.svg.read_text()


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
    for label in shield.labels:
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
) -> npc_shields.types.Shield:
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


def get_shields() -> tuple[npc_shields.types.Shield, ...]:
    """
    All known shields, sorted by drawing ID.

    >>> x = get_shields()
    """
    return tuple(
        sorted(
            (v for v in globals().values() if isinstance(v, npc_shields.types.Shield)),
            key=lambda x: x.drawing_id,
        )
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
