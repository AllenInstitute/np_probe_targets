"""
Protocols and type aliases for implants and related models, for type-checking (MyPy).
"""

from __future__ import annotations

import pathlib
import typing
from collections.abc import Iterable, MutableMapping
from typing import Any, Protocol, Union

import npc_session
from typing_extensions import TypeAlias

InsertionProbeMap: TypeAlias = MutableMapping[str, Union[str, None]]
"""Mapping of probe letter to insertion hole in shield, or None if not inserted.
e.g `{"A": "A1", "B": "B2", "C": None, "D": "E2", "E": "E1", "F": "F1"}`
"""


@typing.runtime_checkable
class Shield(Protocol):
    """A specific implant with a diagram and labelled holes"""

    @property
    def name(self) -> str:
        """Colloquial name for the shield, e.g. '2002', 'Templeton'"""
        ...

    @property
    def drawing_id(self) -> int | str:
        """ID of drawing, e.g. from MPE: '0283-200-002'"""
        ...

    @property
    def labels(self) -> Iterable[str]:
        """Original labels for each hole: e.g. A1, A2, A3, B1, B2, B3, B4, etc."""
        ...

    @property
    def svg(self) -> pathlib.Path:
        """Path to SVG diagram of the shield, with labelled holes as text elements"""
        ...

    def __hash__(self) -> int:
        ...


class Insertion(Protocol):
    """A set of probes inserted (or planned to be inserted) into a shield."""

    @property
    def shield(self) -> Shield:
        """The shield that this probe group was or will be inserted into."""
        ...

    @property
    def probes(self) -> InsertionProbeMap:
        """A record of which probes were inserted into which holes in the shield,
        or a set of targets for planned insertions."""
        ...

    @property
    def notes(self) -> dict[str | npc_session.ProbeRecord, str | None]:
        """Text notes for each probe's insertion."""
        ...

    def to_svg(self) -> str:
        """Get the SVG diagram of the shield with inserted probes labelled."""
        ...

    def to_json(self) -> dict[str, Any]:
        """Get a JSON-serializable representation of the insertion."""
        ...


class InsertionRecord(Insertion, Protocol):
    """A record of a set of probes inserted into a shield."""

    @property
    def session(self) -> npc_session.SessionRecord:
        """Record of the session, including subject, date, session index."""
        ...

    @property
    def experiment_day(self) -> int:
        """1-indexed day of experiment for the subject specified in `session`."""
        ...
