from __future__ import annotations

import dataclasses
import datetime
from collections.abc import Sequence
from typing import Any, Literal

import npc_session
import pydantic

import npc_shields.shields
import npc_shields.types

class Injection(pydantic.BaseModel):
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
    class Config:
        arbitrary_types_allowed=True

    @pydantic.field_serializer('shield', when_used='always')
    def serialize_shield_field(self, shield: npc_shields.types.Shield) -> dict[str, Any]:
        return shield.to_json() if shield is not None else None

    target_structure: str
    """The intended brain structure for the injection ('VISp' etc.)."""

    hemisphere: Literal["left", "right"] = "left"
    """The hemisphere of the brain where the injection was made ('left' or 'right')."""

    depth_um: float
    """Depth of the injection, in microns from brain surface."""

    substance: str = "muscimol"
    """Name of the injected substance."""

    manufacturer: str | None = "Sigma-Aldrich"
    """Manufacturer of the injected substance."""

    identifier: str | None = "M1523"
    """Identifier of the injected substance (e.g. manufacture serial number)."""

    total_volume_nl: float
    """Total volume injected, in nanoliters."""

    concentration_mg_ml: float | None
    """Concentration of the injected substance in milligrams per milliliter."""

    flow_rate_nl_s: float
    """Flow rate of the injection in nanoliters per second."""

    start_time: datetime.datetime = datetime.datetime.now()
    """Time of the first injection, as a datetime object."""

    @pydantic.field_serializer('start_time', when_used='always')
    def serialize_start_time_field(self, start_time: datetime.datetime) -> str:
        return start_time.isoformat(sep=' ', timespec='seconds')

    is_anaesthetized: bool
    """Whether the subject was anaesthetized during the injection."""

    number_of_injections: int
    """Number of individual injections made at this site + depth."""

    # args with defaults ----------------------------------------------- #

    shield: npc_shields.types.Shield | None = None
    """The shield through which the injection was made."""

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

    fluorescence_nm: int | None = None
    """Emission wavelength of the substance injected, if it fluoresces."""

    is_control: bool = False
    """Whether the purpose of the injection was a control."""

    notes: str | None = None
    """Text notes for the injection."""

    def to_json(self) -> dict[str, Any]:
        return self.model_dump()


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
    {'injections': [{'target_structure': 'VISp', 'hemisphere': 'left', 'depth_um': 3000.0, 'substance': 'Fluorogold', 'manufacturer': 'Sigma', 'identifier': '12345', 'total_volume_nl': 1.0, 'concentration_mg_ml': 10.0, 'flow_rate_nl_s': 0.1, 'start_time': '2023-01-01 12:00:00', 'is_anaesthetized': False, 'number_of_injections': 3, 'shield': {'name': '2002', 'drawing_id': '0283-200-002'}, 'location': None, 'location_ap': None, 'location_ml': None, 'fluorescence_nm': 500, 'is_control': False, 'notes': 'This was a test injection'}], 'session': '366122_20240101', 'experiment_day': 1}
    """

    injections: Sequence[npc_shields.types.Injection]
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
