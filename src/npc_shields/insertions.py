from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from typing import Any

import npc_session
from typing_extensions import Self

import npc_shields.shields
import npc_shields.types


class OccupiedHoleError(ValueError):
    pass


def validate_probe_insertion(
    shield: npc_shields.types.Shield,
    new_insertion: npc_shields.types.InsertionProbeMap,
    current_insertion: npc_shields.types.InsertionProbeMap | None = None,
) -> None:
    """
    >>> i = Insertion(npc_shields.shields.DR2002)
    >>> validate_probe_insertion(i.shield, {"A": "A1"}, i.probes)
    >>> validate_probe_insertion(i.shield, {"A": "A99"}, i.probes)
    Traceback (most recent call last):
    ...
    ValueError: probe='A' cannot be assigned to hole='A99': not a valid hole in insertion.shield.name='2002'
    """
    new_values = tuple(new_insertion.values())

    for probe, hole in new_insertion.items():
        if hole is None:
            continue
        if hole not in shield.labels:
            raise ValueError(
                f"{probe=} cannot be assigned to {hole=}: not a valid hole in {shield.name=}"
            )


def _get_default_probe_map() -> dict[str, str | None]:
    return dict.fromkeys("ABCDEF", None)


class ValidatedProbeMap(MutableMapping):
    """A dict-like container of probe letters mapped to insertion holes in a
    shield, with validation on assignment.

    - updating values validates that the holes are in the shield and not already
      occupied

    >>> i = ValidatedProbeMap(npc_shields.shields.DR2002)
    >>> i["A"] = "A1"
    >>> i["A"]
    'A1'
    """

    shield: npc_shields.types.Shield
    _probes: dict[str, str | None]

    def __init__(
        self,
        shield: npc_shields.types.Shield,
        probes: dict[str, str | None] | None = None,
    ) -> None:
        self.shield = shield
        self._probes = probes or _get_default_probe_map()
        for k, v in self._probes.items():
            self[k] = v

    def setmany(self, insertion: npc_shields.types.InsertionProbeMap) -> None:
        self.validate(insertion, with_current=False)
        self._probes.update(insertion)

    def validate(
        self,
        insertion: npc_shields.types.InsertionProbeMap,
        with_current: bool = True,
    ) -> None:
        validate_probe_insertion(
            shield=self.shield,
            new_insertion=insertion,
            current_insertion=self if with_current else None,
        )

    def __getitem__(self, key: str) -> str | None:
        return self._probes[key]

    def __setitem__(self, key: str, value: str | None) -> None:
        self.validate({key: value}, with_current=True)
        self._probes[key] = value

    def __iter__(self) -> Iterator[str]:
        return iter(self._probes)

    def __delitem__(self, key: str) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self._probes)


class Insertion:
    """A dict-like container of probe letters mapped to insertion holes in a
    shield, with other properties and methods fulfilling the `Insertion` protocol.

    >>> i = Insertion(npc_shields.shields.DR2002)
    """

    shield: npc_shields.types.Shield
    probes: npc_shields.types.InsertionProbeMap
    notes: dict[str, str | None]

    def __init__(
        self,
        shield: npc_shields.types.Shield,
        probes: dict[str, str | None] | None = None,
        notes: dict[str, str | None] | None = None,
    ) -> None:
        self.shield = shield
        self.probes = ValidatedProbeMap(shield, probes)
        self.notes = notes or _get_default_probe_map()

    def to_json(self) -> dict[str, Any]:
        """
        >>> i = Insertion(npc_shields.shields.DR2002)
        >>> j = i.to_json()
        >>> assert j["shield"]["name"] == "2002"
        """
        return {
            "shield": dict(name=self.shield.name, drawing_id=self.shield.drawing_id),
            "probes": dict(self.probes),
            "notes": self.notes,
        }

    def to_svg(self) -> str:
        return npc_shields.shields.get_svg_data_with_insertions(
            self.shield, self.probes
        )

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        return cls(
            shield=npc_shields.shields.get_shield(data["shield"]["name"]),
            probes=data["probes"],
            notes=data["notes"],
        )


class InsertionRecord(Insertion):
    """A record of a set of probes inserted into a shield in a given session.

    >>> i = Insertion(npc_shields.shields.DR2002)
    >>> i.probes["A"] = "A1"
    >>> i.to_json()["probes"]["A"]
    'A1'
    """

    def __init__(
        self,
        shield: npc_shields.types.Shield,
        session: str | npc_session.SessionRecord,
        experiment_day: int,
        probes: dict[str, str | None] | None = None,
        notes: dict[str, str | None] | None = None,
    ) -> None:
        super().__init__(shield, probes, notes)
        self.session = npc_session.SessionRecord(session)
        self.experiment_day = experiment_day

    @property
    def session(self) -> npc_session.SessionRecord:
        """Record of the session (includes subject, date, session index)."""
        return self._session

    @session.setter
    def session(self, session: str | npc_session.SessionRecord) -> None:
        if getattr(self, "_session", None) is not None:
            raise AttributeError("session cannot be changed once set")
        self._session = npc_session.SessionRecord(session)

    @property
    def experiment_day(self) -> int:
        """1-indexed day of experiment for the subject specified in `session`."""
        return self._experiment_day

    @experiment_day.setter
    def experiment_day(self, experiment_day: int) -> None:
        if getattr(self, "_experiment_day", None) is not None:
            raise AttributeError("experiment_day cannot be changed once set")
        if not isinstance(experiment_day, int):
            raise TypeError(f"{experiment_day=} must be an integer")
        if experiment_day < 1:
            raise ValueError(
                f"{experiment_day=} must be a positive integer greater than 0"
            )
        self._experiment_day = experiment_day

    def to_json(self) -> dict[str, Any]:
        """
        >>> i = InsertionRecord(npc_shields.shields.DR2002, "366122_20240101", 1)
        >>> j = i.to_json()
        >>> assert j["session"] == "366122_20240101"
        """
        return {
            **super().to_json(),
            "session": self.session,
            "experiment_day": self.experiment_day,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        return cls(
            shield=npc_shields.shields.get_shield(data["shield"]["name"]),
            session=data["session"],
            experiment_day=data["experiment_day"],
            probes=data["probes"],
            notes=data["notes"],
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod(
        optionflags=(
            doctest.ELLIPSIS
            | doctest.NORMALIZE_WHITESPACE
            | doctest.FAIL_FAST
            | doctest.IGNORE_EXCEPTION_DETAIL
        )
    )
