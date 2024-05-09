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
    ...     location="D1",
    ...     target_structure="VISp",
    ...     hemisphere="left",
    ...     depth_um=200,
    ...     substance="Fluorogold",
    ...     manufacturer="Sigma",
    ...     identifier="12345",
    ...     total_volume_nl=1.0,
    ...     concentration_mg_ml=10.0,
    ...     flow_rate_nl_s=0.1,
    ...     start_time=datetime.datetime(2023, 1, 1, 12, 0),
    ...     fluorescence_nm=500,
    ...     number_of_injections=3,
    ...     notes="This was a test injection",
    ...     is_control=False,
    ...     is_anaesthetized=True,
    ... )
    """

    shield: npc_shields.types.Shield | None
    """The shield through which the injection was made."""

    target_structure: str
    """The intended brain structure for the injection ('VISp' etc.)."""

    hemisphere: Literal["left", "right"]
    """The hemisphere of the brain where the injection was made ('left' or 'right')."""

    depth_um: float
    """Depth of the injection, in microns from brain surface."""

    substance: str
    """Name of the injected substance."""

    manufacturer: str | None
    """Manufacturer of the injected substance."""

    identifier: str | None
    """Identifier of the injected substance (e.g. manufacture serial number)."""

    total_volume_nl: float
    """Total volume injected, in nanoliters."""

    concentration_mg_ml: float | None
    """Concentration of the injected substance in milligrams per milliliter."""

    flow_rate_nl_s: float
    """Flow rate of the injection in nanoliters per second."""

    start_time: datetime.datetime
    """Time of the first injection, as a datetime object."""

    is_anaesthetized: bool
    """Whether the subject was anaesthetized during the injection."""

    # args with defaults ----------------------------------------------- #

    location: str | None = None
    """The hole in the shield through which the injection was made (e.g. 'C3').

    - alternatively, a string indicating location of a burr hole or other non-shield location.
    """

    location_ap: float | None = None
    """Distance in millimeters from bregma to injection site along
    anterior-posterior axis (+ve is anterior)."""

    location_ml: float | None = None
    """Distance in millimeters from brain midline to injection site along
    medial-lateral axis."""

    fluorescence_nm: float | None = None
    """Emission wavelength of the substance injected, if it fluoresces."""

    number_of_injections: int = 1
    """Number of individual injections made at this site + depth."""

    is_control: bool = False
    """Whether the purpose of the injection was a control."""

    notes: str | None = None
    """Text notes for the injection."""

    def to_json(self) -> dict[str, Any]:
        data = dataclasses.asdict(self)
        if self.shield is not None:
            data["shield"] = self.shield.to_json()
        return data


@dataclasses.dataclass
class InjectionRecord:
    """A record of a set of injections.

    >>> i = Injection(
    ...     shield=npc_shields.shields.DR2002,
    ...     target_structure="VISp",
    ...     hemisphere="left",
    ...     depth_um=3000,
    ...     substance="Fluorogold",
    ...     manufacturer="Sigma",
    ...     identifier="12345",
    ...     total_volume_nl=1.0,
    ...     concentration_mg_ml=10.0,
    ...     flow_rate_nl_s=0.1,
    ...     start_time=datetime.datetime(2023, 1, 1, 12, 0),
    ...     fluorescence_nm=500,
    ...     number_of_injections=3,
    ...     notes="This was a test injection",
    ...     is_control=False,
    ...     is_anaesthetized=False,
    ... )
    >>> r = InjectionRecord(
    ...     injections=[i],
    ...     session="366122_20240101",
    ...     experiment_day=1,
    ... )
    >>> r.to_json()
    {'injections': [{'shield': {'name': '2002', 'drawing_id': '0283-200-002'}, 'target_structure': 'VISp', 'hemisphere': 'left', 'depth_um': 3000, 'substance': 'Fluorogold', 'manufacturer': 'Sigma', 'identifier': '12345', 'total_volume_nl': 1.0, 'concentration_mg_ml': 10.0, 'flow_rate_nl_s': 0.1, 'start_time': datetime.datetime(2023, 1, 1, 12, 0), 'is_anaesthetized': False, 'location': None, 'location_ap': None, 'location_ml': None, 'fluorescence_nm': 500, 'number_of_injections': 3, 'is_control': False, 'notes': 'This was a test injection'}], 'session': '366122_20240101', 'experiment_day': 1}
    """

    injections: Sequence[Injection]
    """A record of each injection made."""

    session: str | npc_session.SessionRecord
    """Record of the session, including subject, date, session index."""

    experiment_day: int
    """1-indexed day of experiment for the subject specified in `session`."""

    def to_json(self) -> dict[str, Any]:
        """Get a JSON-serializable representation of the injections."""
        return {
            "injections": [injection.to_json() for injection in self.injections],
            "session": self.session,
            "experiment_day": self.experiment_day,
        }


if __name__ == "__main__":
    import doctest

    doctest.testmod()
