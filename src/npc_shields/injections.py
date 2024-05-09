from __future__ import annotations

import dataclasses
import datetime
from collections.abc import Sequence
from typing import Any, Literal

import npc_session

import npc_shields.shields
import npc_shields.types


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Injection:
    """An injection through a hole in a shield at a particular brain location (site + depth).

    - should allow for no shield (e.g. burr hole)
    - should record hemisphere
    - may consist of multiple individual injections

    >>> i = Injection(
    ...     shield=npc_shields.shields.DR2002,
    ...     location="A1",
    ...     hemisphere="left",
    ...     depth_um=3000,
    ...     substance="Fluorogold",
    ...     manufacturer="Sigma",
    ...     identifier="12345",
    ...     total_volume_ul=1.0,
    ...     concentration_mg_ml=10.0,
    ...     flow_rate_ul_s=0.1,
    ...     start_time=datetime.datetime(2023, 1, 1, 12, 0),
    ...     fluorescence_nm=500,
    ...     number_of_injections=3,
    ...     notes="This was a test injection",
    ...     is_control=False,
    ... )
    """

    shield: npc_shields.types.Shield | None
    """The shield through which the injection was made."""

    location: str
    """The hole in the shield through which the injection was made (e.g. 'C3').

    - alternatively, a string indicating location of a burr hole or other non-shield location.
    """

    hemisphere: Literal['left', 'right']
    """The hemisphere of the brain where the injection was made (e.g. 'left', 'right')."""

    depth_um: float
    """Depth of the injection, in microns from brain surface."""

    substance: str
    """Name of the injected substance."""

    manufacturer: str | None
    """Manufacturer of the injected substance."""

    identifier: str | None
    """Identifier of the injected substance (e.g. manufacture serial number)."""

    total_volume_ul: float
    """Total volume injected, in microliters."""

    concentration_mg_ml: float | None
    """Concentration of the injected substance in milligrams per milliliter."""

    flow_rate_ul_s: float
    """Flow rate of the injection in microliters per second."""

    start_time: datetime.datetime
    """Time of the first injection, as a datetime object."""

    # args with defaults ----------------------------------------------- #

    fluorescence_nm: float | None = None
    """Wavelength of fluorescence for the injection."""

    number_of_injections: int = 1
    """Number of individual injections made at this site + depth."""

    is_control: bool = False
    """Whether the purpose of the injection was a control."""

    notes: str | None = None
    """Text notes for the injection."""


@dataclasses.dataclass
class InjectionRecord:
    """A record of a set of injections.

    >>> i = Injection(
    ...     shield=npc_shields.shields.DR2002,
    ...     location="A1",
    ...     hemisphere="left",
    ...     depth_um=3000,
    ...     substance="Fluorogold",
    ...     manufacturer="Sigma",
    ...     identifier="12345",
    ...     total_volume_ul=1.0,
    ...     concentration_mg_ml=10.0,
    ...     flow_rate_ul_s=0.1,
    ...     start_time=datetime.datetime(2023, 1, 1, 12, 0),
    ...     fluorescence_nm=500,
    ...     number_of_injections=3,
    ...     notes="This was a test injection",
    ...     is_control=False,
    ... )
    >>> r = InjectionRecord(
    ...     injections=[i],
    ...     session="366122_20240101",
    ...     experiment_day=1,
    ... )
    >>> r.to_json()
    {'injections': [{'shield': {'name': '2002', 'drawing_id': '0283-200-002', 'labels': ('A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4', 'D1', 'D2', 'D3', 'E1', 'E2', 'E3', 'E4', 'F1', 'F2', 'F3'), 'svg': WindowsPath('C:/Users/ben.hardcastle/github/np_probe_targets/src/npc_shields/drawings/2002.svg')}, 'location': 'A1', 'hemisphere': 'left', 'depth_um': 3000, 'substance': 'Fluorogold', 'manufacturer': 'Sigma', 'identifier': '12345', 'total_volume_ul': 1.0, 'concentration_mg_ml': 10.0, 'flow_rate_ul_s': 0.1, 'start_time': datetime.datetime(2023, 1, 1, 12, 0), 'fluorescence_nm': 500, 'number_of_injections': 3, 'is_control': False, 'notes': 'This was a test injection'}], 'session': '366122_20240101', 'experiment_day': 1}
    """

    injections: Sequence[Injection]
    """A record of each injection made."""

    session: str | npc_session.SessionRecord
    """Record of the session, including subject, date, session index."""

    experiment_day: int
    """1-indexed day of experiment for the subject specified in `session`."""


    def to_json(self)-> dict[str, Any]:
        """Get a JSON-serializable representation of the injections."""
        return {
            'injections': [dataclasses.asdict(injection) for injection in self.injections],
            'session': self.session,
            'experiment_day': self.experiment_day,
        }

if __name__ == "__main__":
    import doctest
    doctest.testmod()
