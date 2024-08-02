from __future__ import annotations

import dataclasses
import datetime
from collections.abc import Iterable
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
    ...     shield_hole="D1",
    ...     target_structure="VISp",
    ...     hemisphere="left",
    ...     depth_um=200,
    ...     substance="Fluorogold",
    ...     manufacturer="Sigma",
    ...     identifier="12345",
    ...     total_volume_nl=1.0,
    ...     concentration_mg_ml=10.0,
    ...     flow_rate_nl_s=0.1,
    ...     pipette_inner_diameter_um=22.88,
    ...     start_time=datetime.datetime(2023, 1, 1, 12, 0),
    ...     settle_time_s=60,
    ...     fluorescence_nm=500,
    ...     notes="This was a test injection",
    ...     is_control=False,
    ...     is_anaesthetized=True,
    ...     is_mixed_correctly=True,
    ... )
    """

    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        frozen=True,
    )

    shield: npc_shields.types.Shield | None = None
    """The shield through which the injection was made."""

    @pydantic.field_serializer("shield", when_used="always")
    def serialize_shield_field(
        self, shield: npc_shields.types.Shield
    ) -> dict[str, Any]:
        return shield.to_json() if shield is not None else None

    shield_hole: str | None = None
    """The hole in the shield through which the injection was made (e.g. 'C3')."""

    target_structure: str
    """The intended brain structure for the injection ('VISp' etc.)."""

    hemisphere: Literal["left", "right"] = "left"
    """The hemisphere of the brain where the injection was made ('left' or 'right')."""

    depth_um: float
    """Depth of the injection, in microns from brain surface."""

    location_ap: float | None = None
    """Distance in millimeters from bregma to injection site along
    anterior-posterior axis (+ve is anterior)."""

    location_ml: float | None = None
    """Distance in millimeters from brain midline to injection site along
    medial-lateral axis."""

    substance: str = "muscimol"
    """Name of the injected substance."""

    fluorescence_nm: int | None = None
    """Emission wavelength of the substance injected, if it fluoresces."""

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

    @pydantic.field_serializer("start_time", when_used="always")
    def serialize_start_time_field(self, start_time: datetime.datetime) -> str:
        return start_time.isoformat(sep=" ", timespec="seconds")

    settle_time_s: float | None = None
    """Time waited after injection before changing depth, in seconds."""

    pipette_inner_diameter_um: float | None = None
    """Inner diameter of the pipette used for the injection, in microns."""

    is_anaesthetized: bool
    """Whether the subject was anaesthetized during the injection."""

    is_control: bool
    """Whether the purpose of the injection was a control."""

    is_mixed_correctly: bool | None = None
    """An early batch of muscimol may not have been mixed correctly"""

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
    ...     notes="This was a test injection",
    ...     is_control=False,
    ...     is_anaesthetized=False,
    ... )
    >>> r = InjectionRecord(
    ...     injections=[i],
    ...     session="366122_20240101",
    ...     injection_day_index=1,
    ... )
    >>> r.to_json()
    {'injections': [{'shield': {'name': '2002', 'drawing_id': '0283-200-002'}, 'shield_hole': None, 'target_structure': 'VISp', 'hemisphere': 'left', 'depth_um': 3000.0, 'location_ap': None, 'location_ml': None, 'substance': 'Fluorogold', 'fluorescence_nm': 500, 'manufacturer': 'Sigma', 'identifier': '12345', 'total_volume_nl': 1.0, 'concentration_mg_ml': 10.0, 'flow_rate_nl_s': 0.1, 'start_time': '2023-01-01 12:00:00', 'settle_time_s': None, 'pipette_inner_diameter_um': None, 'is_anaesthetized': False, 'is_control': False, 'is_mixed_correctly': None, 'notes': 'This was a test injection'}], 'session': '366122_20240101', 'injection_day_index': 1}
    """

    injections: Iterable[npc_shields.types.Injection]
    """A record of each injection made."""

    session: str | npc_session.SessionRecord
    """Record of the session, including subject, date, session index."""

    injection_day_index: int
    """1-indexed day of experiment for the subject specified in `session`."""

    def to_json(self) -> dict[str, Any]:
        """Get a JSON-serializable representation of the injections."""
        return {
            "injections": [injection.to_json() for injection in self.injections],
            "session": self.session,
            "injection_day_index": self.injection_day_index,
        }


if __name__ == "__main__":
    import doctest

    doctest.testmod()
