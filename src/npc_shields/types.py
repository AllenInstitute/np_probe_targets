"""
Protocols and type aliases for implants and related models, for type-checking (MyPy).
"""

from __future__ import annotations

import datetime
import pathlib
import typing
from collections.abc import Iterable, MutableMapping, Sequence
from typing import Any, Literal, Protocol, Union

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

    def to_json(self) -> dict[str, Any]:
        """Get a JSON-serializable representation of the shield."""
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


class Injection(Protocol):
    """An injection through a hole in a shield at a particular brain location (site + depth).

    - should allow for no shield (e.g. burr hole)
    - should record hemisphere
    - may consist of multiple individual injections
    """

    @property
    def shield(self) -> Shield | None:
        """The shield through which the injection was made."""
        ...

    @property
    def location(self) -> str:
        """The hole in the shield through which the injection was made (e.g. 'C3').

        - alternatively, a string indicating location of a burr hole or other non-shield location.
        """
        ...

    @property
    def location_ap(self) -> float | None:
        """Distance in millimeters from bregma to injection site along
        anterior-posterior axis (+ve is anterior)."""
        ...

    @property
    def location_ml(self) -> float | None:
        """Distance in millimeters from brain midline to injection site along
        medial-lateral axis."""
        ...

    @property
    def target_structure(self) -> str:
        """The intended brain structure for the injection ('VISp' etc.)."""
        ...

    @property
    def hemisphere(self) -> Literal["left", "right"]:
        """The hemisphere of the brain where the injection was made (e.g. 'left', 'right')."""
        ...

    @property
    def depth_um(self) -> float:
        """Depth of the injection, in microns from brain surface."""
        ...

    @property
    def fluorescence_nm(self) -> float | None:
        """Wavelength of fluorescence for the injection."""
        ...

    @property
    def manufacturer(self) -> str | None:
        """Manufacturer of the injected substance."""
        ...

    @property
    def substance(self) -> str:
        """Name of the injected substance."""
        ...

    @property
    def identifier(self) -> str | None:
        """Identifier of the injected substance (e.g. manufacture serial number)."""
        ...

    @property
    def concentration_mg_ml(self) -> float | None:
        """Concentration of the injected substance in milligrams per milliliter."""
        ...

    @property
    def flow_rate_nl_s(self) -> float:
        """Flow rate of the injection in nanoliters per second."""
        ...

    @property
    def number_of_injections(self) -> int:
        """Number of individual injections made at this site + depth."""
        ...

    @property
    def total_volume_nl(self) -> float:
        """Total volume injected, in nanoliters."""
        ...

    @property
    def start_time(self) -> datetime.datetime:
        """Time of the first injection, as a datetime object."""
        ...

    @property
    def is_anaesthetized(self) -> bool:
        """Whether the subject was anaesthetized during the injection."""
        ...

    @property
    def is_control(self) -> bool:
        """Whether the purpose of the injection was a control."""
        ...

    @property
    def notes(self) -> str | None:
        """Text notes for the injection."""
        ...

    def to_json(self) -> dict[str, Any]:
        """Get a JSON-serializable representation of the injection."""
        ...


class InjectionRecord(Protocol):
    """A record of a set of injections in a session."""

    @property
    def injections(self) -> Sequence[Injection]:
        """A record of each injection made."""
        ...

    @property
    def session(self) -> npc_session.SessionRecord:
        """Record of the session, including subject, date, session index."""
        ...

    @property
    def experiment_day(self) -> int:
        """1-indexed day of experiment for the subject specified in `session`."""
        ...

    def to_json(self) -> dict[str, Any]:
        """Get a JSON-serializable representation of the injections in a session."""
        ...
