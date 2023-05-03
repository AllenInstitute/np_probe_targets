"""Models for Neuropixels probe insertion info (providing suggested targets,
recording actual insertions, storing notes) and properties of an implanted plastic
skull-replacement with holes that provide access for probes to enter the brain (CAD
diagram, hole positions, hole labels). Views are provided for displaying probe
configurations relative to an implant template, with controllers that impose physical
rules (e.g. two probes can't occupy one hole in an implant). 

Overview of classes
- a Probe has a letter and other info
- a ProbeGroup has Probes for a given experiment
- ImplantHoles is a layout of holes for Probes on a specific implant
- a Drawing has data and methods for rendering ImplantHoles and Probes on a drawing of
an implant

"""
from __future__ import annotations

import collections
import datetime
import functools
import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Literal, Type

import IPython.display
import ipywidgets as ipw

COUNT_OF_SKIPPED_WEEKS_IN_DR_PLAN = 8
"Keep a tally of weeks with no DR experiments: increment as needed"

DR_PROBE_INSERTION_RECORDS_DIR = pathlib.Path(
    "//allen/programs/mindscope/workgroups/dynamicrouting/ben/implants/insertion_records"
)
TEMPLETON_PROBE_INSERTION_RECORDS_DIR = pathlib.Path(
    "//allen/programs/mindscope/workgroups/dynamicrouting/ben/templeton/insertion_records"
)


class ImplantHoles:
    "Establishes the labels of available holes for an implant."
    hole_labels: tuple[str, ...]
    "Original labels for each hole: e.g. A1, A2, A3, B1, B2, B3, B4, etc."


class TS5(ImplantHoles):
    "First production DR implant, known as DR1, TS-5, or 2002."
    probe_hole_idx = {
        "A": [1, 2, 3],
        "B": [1, 2, 3, 4],
        "C": [1, 2, 3, 4],
        "D": [1, 2, 3],
        "E": [1, 2, 3, 4],
        "F": [1, 2, 3],
    }
    "1-indexed hole indices available for each probe."
    hole_labels: tuple[str, ...] = tuple(
        f"{probe}{index}"
        for probe, indices in probe_hole_idx.items()
        for index in indices
    )
    "Original labels for each hole: A1, A2, A3, B1, B2, B3, B4, etc."
    probe_letters: tuple[str, ...] = tuple(probe_hole_idx.keys())
    "Probe letters: A, B, C, D, E, F."


class Templeton(ImplantHoles):
    """Templeton implant - MPE drawing 0283-200-001"""
    probe_hole_idx = {
        "A": [1, 2, 3],
        "B": [1, 2, 3],
        "C": [1, 2, 3, 4],
        "D": [1,],
        "E": [],
        "F": [1, 2],
    }
    "1-indexed hole indices available for each probe."
    hole_labels: tuple[str, ...] = tuple(
        f"{probe}{index}"
        for probe, indices in probe_hole_idx.items()
        for index in indices
    )
    "Original labels for each hole: A1, A2, A3, B1, B2, B3, B4, etc."
    probe_letters: tuple[str, ...] = tuple(probe_hole_idx.keys())
    "Probe letters: A, B, C, D, F."
    
    
@dataclass
class Probe:
    letter: str
    hole: str | None = None
    notes: str | None = None


class ProbeGroup(collections.UserDict):
    """User-facing container for Probe objects, which may have holes, notes, etc. assigned.
    Behaves like a dictionary of `probe letters : hole labels`."""

    available_hole_labels: tuple[str, ...]
    "Implant-specific property"
    available_probe_letters: tuple[str, ...]
    "Implant-specific property"

    def __init__(
        self,
        hole_labels: Mapping | Sequence[int | str | None],
        probe_letters: Sequence[str] = "ABCDEF",
        **kwargs,
    ):
        "Create a dictionary of probe letters to hole labels"
        hole_labels, probe_letters = self.parse_hole_inputs(
            hole_labels, probe_letters
        )
        self._probes = tuple(Probe(probe_letter) for probe_letter in probe_letters)
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(self.__dict__())
        self.update_probe_holes(dict(zip(probe_letters, hole_labels)))

    def __dict__(self):
        return dict(zip(self.probe_letters, self.hole_labels))

    def __setitem__(self, key, item):
        "Update the dictionary and the relevant Probe object."
        if key in self.data.keys() and self.data[key] == item:
            return
        self.validate_probe_letter(key)
        self.validate_hole_label(item)
        self.data[key] = item
        if len(self.data) == len(self._probes):
            self.update_probe_holes(dict(self))

    @property
    def probe(self) -> dict[str, Probe]:
        "Dictionary of probe letters to Probe objects."
        return dict(zip([probe.letter for probe in self._probes], self._probes))

    def update_probe_holes(self, probe_holes: Mapping):
        "Apply new probe -> hole assignments and sync the dictionary."
        hole_labels, probe_letters = self.parse_hole_inputs(probe_holes)
        for probe, hole in dict(zip(probe_letters, hole_labels)).items():
            # update Probe objects
            if hole and hole.lower() == "none":
                hole = None
            self.probe[probe].hole = hole
            # update dictionary
            if probe not in self.keys() or self.data[probe] != hole:
                self.data[probe] = hole

    @property
    def probe_letters(self) -> Sequence[str]:
        "Capital letter for each probe. e.g. `'A','B','C'`"
        return tuple(probe.letter for probe in self._probes)

    @property
    def hole_labels(self) -> Sequence[None | str]:
        "Identifier for hole assigned to each probe, if any, e.g. `'A1','B2'`"
        return tuple(probe.hole for probe in self._probes)

    @classmethod
    def validate_probe_letter(cls, probe_letter: str):
        if probe_letter not in cls.available_probe_letters:
            raise ValueError(
                f"Probe letter must be one of {cls.available_probe_letters}: {probe_letter=}"
            )

    @classmethod
    def validate_hole_label(cls, hole_label: str | None):
        if hole_label and hole_label.lower() == "none":
            hole_label = None
        if hole_label not in [None, *cls.available_hole_labels]:
            raise ValueError(
                f"Label must be a probe+index combo string ('A1', 'B2', etc.): {hole_label=}"
            )

    @classmethod
    def validate_hole_index_for_probe(cls, probe_letter: str, hole_index: int | None):
        "Preferred over validate_hole_label as it specifies available hole indices for probe."
        if (
            hole_index
            and f"{probe_letter}{hole_index}" not in cls.available_hole_labels
        ):
            raise ValueError(
                f"Holes available for {probe_letter} are {[label[1:] for label in cls.available_hole_labels if label.startswith(probe_letter)]}: {hole_index=}"
            )

    @classmethod
    def probe_letter_and_hole_index_from_label(
        cls, label: str
    ) -> tuple[str, int] | tuple[None, None]:
        "Convert a hole label, e.g. 'A1', to a probe letter and hole index"
        if label is None:
            return None, None
        if not isinstance(label, str):
            raise TypeError(
                f"Label must be a string, e.g. 'A1': {label=}, {type(label)=}"
            )
        probe_letter = label[0].upper()
        cls.validate_probe_letter(probe_letter)
        hole_index = int(label[1:])
        cls.validate_hole_index_for_probe(probe_letter, hole_index)
        return probe_letter, hole_index

    @classmethod
    def parse_hole_inputs(
        cls,
        hole_input: Sequence[str | int | None] | Mapping[str, int | str | None],
        probe_letters: Sequence[str] = None,
    ) -> tuple[tuple[str | None, ...], tuple[str, ...]]:
        "Convert inputs into a sequence of hole labels, ordered by probe letter."

        if probe_letters is None:
            probe_letters = cls.available_probe_letters[: len(hole_input)]
        if len(hole_input) != len(probe_letters):
            raise ValueError(
                f"holes input must be a sequence with the same length as probe_letters, using None entries to fill gaps as required: {len(probe_letters)}: {len(hole_input)=}"
            )

        hole_output: Sequence[Optional[str]] = []

        # deal with mapping -------------------------------------------------------------------- #
        if isinstance(hole_input, dict):
            hole_input = {
                k: v for k, v in sorted(hole_input.items(), key=lambda i: i[0])
            }
            # validate values by passing back through this function
            hole_output, probe_letters = cls.parse_hole_inputs(
                list(hole_input.values()), list(hole_input.keys())
            )

        # deal with lists ---------------------------------------------------------------------- #
        elif all(isinstance(i, int) or i is None for i in hole_input):
            hole_output = []
            for probe, hole in zip(probe_letters, hole_input):
                if hole is None:
                    hole_output.append(None)
                else:
                    hole_output.append(f"{probe}{hole}")

        elif all(isinstance(i, str) or i is None for i in hole_input):
            hole_output = [i for i in hole_input]

        # validate labels by attempting to convert label (A1 expected) to probe and hole
        map(cls.probe_letter_and_hole_index_from_label, hole_output)

        return tuple(hole_output), tuple(probe_letters)

    @property
    def notes(self) -> dict:
        "Notes for each probe"
        return {p.letter: p.notes for p in self._probes}

    @notes.setter
    def notes(self, notes: dict[str, str | None]):
        if not isinstance(notes, dict):
            raise TypeError(
                f"Notes must be a dict `probe_letter:note`: {notes=}, {type(notes)=}"
            )
        for probe_letter, note in notes.items():
            self.validate_probe_letter(probe_letter)
            self.add_notes_to_probe(note, probe_letter)

    def add_notes_to_probe(self, notes: str | None, probe_letter: str):
        "Add notes to a specific probe"
        if notes is None:
            return
        self.validate_probe_letter(probe_letter)
        if not isinstance(notes, str):
            raise TypeError(f"Notes must be a string: {notes=}, {type(notes)=}")
        self.probe[probe_letter].notes = notes

    def save_to_json(
        self, path: pathlib.Path, probe_group_name: str = "probe_group", **kwargs
    ):
        "Save to a JSON file, appending if file already exists."
        path = pathlib.Path(path).with_suffix(".json")

        dump = dict()

        dump[probe_group_name] = {
            f"probe{p.letter}": p.__dict__ for p in self.probe.values()
        }

        for k, v in kwargs.items():
            dump[probe_group_name][k] = v

        strfmt = "%Y%m%d%H%M"
        dump[probe_group_name][f"saved_{strfmt}"] = datetime.datetime.now().strftime(
            strfmt
        )

        try:
            if path.exists():
                with open(path, "r") as f:
                    data = json.load(f)
                data[probe_group_name].update(dump[probe_group_name])
            else:
                raise FileNotFoundError
        except OSError:
            data = dump
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_json(self, path: pathlib.Path, probe_group_name: str = "probe_group"):
        "Load probe group from a JSON file."
        path = pathlib.Path(path).with_suffix(".json")
        with open(path, "r") as f:
            data = json.load(f)
        data = data[probe_group_name]

        probe_holes = {
            v["letter"]: v["hole"] for k, v in data.items() if k.startswith("probe")
        }

        self.__init__(probe_holes)
        for k, v in data.items():
            try:
                self.add_notes_to_probe(v["notes"], v["letter"])
            except:
                pass
    
class TS5ProbeGroup(ProbeGroup):
    """User-facing container for Probe objects, which may have holes, notes, etc. assigned.
    Behaves like a dictionary of `probe letters : hole labels`."""

    available_hole_labels: tuple[str, ...] = TS5.hole_labels
    "Implant-specific property"
    available_probe_letters: tuple[str, ...] = TS5.probe_letters
    "Implant-specific property"

class TempletonProbeGroup(ProbeGroup):
    """User-facing container for Probe objects, which may have holes, notes, etc. assigned.
    Behaves like a dictionary of `probe letters : hole labels`."""

    available_hole_labels: tuple[str, ...] = Templeton.hole_labels
    "Implant-specific property"
    available_probe_letters: tuple[str, ...] = Templeton.probe_letters
    "Implant-specific property"
    

class ProbeInsertionsTS5(TS5ProbeGroup):
    "Record of actual insertions for a given recording."

    save_dir: pathlib.Path = DR_PROBE_INSERTION_RECORDS_DIR
    probe_group_name = "probe_insertions"


    def __init__(self, *args, **kwargs):
        if not args and "day" in kwargs:
            self.load(*args, **kwargs)
            self._from_record = True
        else:
            super().__init__(*args, probe_letters="ABCDEF", **kwargs)
            self._from_record = False

    @property
    def from_record(self) -> bool:
        "Whether this probe group was loaded from a record of insertions saved to disk."
        return self._from_record

    def filename(self, day: Literal[1, 2, 3, 4] = None, date: datetime.date = None):
        if date is None:
            date = datetime.date.today()
        return f"{date:%Y%m%d}_{str(day) + '_' if day is not None else ''}probe_insertions.json"

    def save(self, day: Literal[1, 2, 3, 4] = None, **kwargs):
        "Write probe info to a JSON file, adding extra fields as kwargs."
        day = self.day if day is None and hasattr(self, "day") else day
        path = self.save_dir / self.filename(day=day)
        kwargs["implant"] = "TS-5/2002/DR1"
        kwargs["day_1-4"] = day
        super().save_to_json(
            path=path, probe_group_name=self.probe_group_name, **kwargs
        )

    def load(
        self,
        day: Literal[1, 2, 3, 4],
        date_in_target_week: datetime.date = None,
        **kwargs,
    ):
        if date_in_target_week is None:
            date_in_target_week = datetime.date.today()

        # actual save date isn't predictable, so we search for a file with the correct
        # 'day' saved that week, starting on Monday...
        date_in_target_week -= datetime.timedelta(days=date_in_target_week.weekday())
        for _ in range(4):
            path = self.save_dir / self.filename(date=date_in_target_week, day=day)
            if path.exists():
                break
            date_in_target_week += datetime.timedelta(days=1)
        else:
            raise FileNotFoundError(
                f"No probe insertion records found for day {day} of week {date_in_target_week}"
            )

        super().load_from_json(path, probe_group_name=self.probe_group_name, **kwargs)


class ProbeInsertionsTempleton(ProbeInsertionsTS5):
    "Record of actual insertions for a given recording."

    save_dir: pathlib.Path = TEMPLETON_PROBE_INSERTION_RECORDS_DIR
    
    available_hole_labels: tuple[str, ...] = Templeton.hole_labels
    "Implant-specific property"
    available_probe_letters: tuple[str, ...] = Templeton.probe_letters
    "Implant-specific property"
    
    def save(self, day: Literal[1, 2, 3, 4] = None, **kwargs):
        "Write probe info to a JSON file, adding extra fields as kwargs."
        day = self.day if day is None and hasattr(self, "day") else day
        path = self.save_dir / self.filename(day=day)
        kwargs["implant"] = "Templeton/v1/0283-200-001"
        kwargs["day_1-4"] = day
        super().save_to_json(
            path=path, probe_group_name=self.probe_group_name, **kwargs
        )
        
    
class ProbeTargetsFromPlanTS5(TS5ProbeGroup):
    """Insertion targets for a given week, as specified by Corbett's plan.

    The plan has 8 weeks, two sets of targets per week:
    - first set for recordings on day 1 and day 3,
    - second set for recordings on day 2 and day 4.
    """

    plan = (
        ((1, 1, 1, 1, 1, 1), (2, 2, 2, 2, 2, 2)),
        ((1, 1, 1, 2, 2, 2), (2, 2, 2, 1, 1, 1)),
        ((1, 2, 2, 1, 1, 2), (2, 1, 1, 2, 2, 1)),
        ((1, 2, 2, 2, 2, 1), (2, 1, 1, 1, 1, 2)),
        ((2, 1, 2, 1, 2, 1), (1, 2, 1, 2, 1, 2)),
        ((2, 2, 1, 2, 1, 1), (1, 1, 2, 1, 2, 2)),
        ((2, 1, 2, 2, 1, 2), (1, 2, 1, 1, 2, 1)),
        ((2, 2, 1, 1, 2, 2), (1, 1, 2, 2, 1, 1)),
    )
    "Target holes (1-indexed) for each probe (x6), for each day (x2), for each week (x8)"
    first_week = datetime.date(2022, 10, 17)  # Oct 17-21
    "First week of planned probe assignments for TS5 implant"
    skipped_weeks: int = COUNT_OF_SKIPPED_WEEKS_IN_DR_PLAN
    "Tally of weeks with no DR exps"

    def __init__(self, day: Literal[1, 2, 3, 4], *args, week: Optional[int] = None, **kwargs):
        if week is None:
            week = self.get_plan_week()
        self.week = week
        targets = self.targets_by_day_and_week(week=self.week, day=day)
        super().__init__(hole_labels=targets, probe_letters="ABCDEF", *args, **kwargs)

    @classmethod
    def get_plan_week(cls) -> int:
        "Number of weeks since start of plan (1-indexed)"
        weeks_since_first_week = int((datetime.date.today() - cls.first_week).days / 7)
        return 1 + max(
            0, weeks_since_first_week - cls.skipped_weeks
        )  # minimum of week 1

    @classmethod
    def targets_by_day_and_week(
        cls, day: Literal[1, 2, 3, 4], week: int = None
    ) -> tuple[int, ...]:
        "Return the target holes for a given day (1-4) and week (1-8), defaulting to week since start of plan"
        if week is None:
            week = cls.get_plan_week()
        if any(v == 0 for v in (week, day)):
            raise ValueError(
                f"Day and week are 1-indexed: {day=}, {week=} (0 is not allowed)"
            )
        day = (day - 1) % 2
        week = (week - 1) % 8
        return cls.plan[week][day]
    
    
class DrawingSVG:
    """Functions for controlling and altering graphic representation of ProbeGroups on implant image,
    but not functions for displaying it."""

    svg_path: pathlib.Path
    ".svg of implant"
    
    implant: ImplantHoles
    probes: Type[ProbeGroup]
    
    def __init__(
        self, probe_hole_assignments: ProbeGroup | Sequence | Mapping = None, **kwargs
    ):
        if isinstance(probe_hole_assignments, ProbeGroup):
            self.current_probe_hole_assignments: dict[
                str, str | None
            ] = probe_hole_assignments
        else:
            self.current_probe_hole_assignments: dict[str, str | None] = self.probes(
                probe_hole_assignments
            )
            "Holes for each probe to be drawn on implant"
        self.previous_probe_hole_assignments: dict[str, str | None] = self.probes(
            [None] * len(self.current_probe_hole_assignments)
        )
        "Last-known assigned holes, in case we need to 'undo' a probe-hole assignment"

    @classmethod
    def get_svg_data(cls) -> str:
        """Raw SVG data is XML, which can be parsed or used as a string, updated then displayed as HTML"""
        return cls.svg_path.read_text()
        
    @property
    def drawing_with_current_probe_hole_assignments(self) -> str:
        "Updated SVG code with current target holes"
        self.resolve_current_probe_hole_assignments()
        return self.add_probe_hole_assignments_to_svg(
            self.current_probe_hole_assignments
        )
        # return self.add_probe_hole_assignments_to_svg(self.hole_label_to_probe_map)

    @classmethod
    def add_probe_hole_assignments_to_svg(
        cls, probe_hole_assignments: Sequence | Mapping | ProbeGroup
    ) -> str:
        "Add probe-assigned holes to stored SVG data"
        if not isinstance(probe_hole_assignments, ProbeGroup):
            probe_hole_assignments = ProbeGroup(probe_hole_assignments)
        data: str = cls.get_svg_data()
        reverse_mapping = {v: k for k, v in probe_hole_assignments.items()}

        for textlabel in cls.implant.hole_labels:
            # for hole, textlabel in dict(probe_hole_assignments).items():
            if textlabel not in probe_hole_assignments.values():
                data = data.replace(f">{textlabel}</tspan>", f"></tspan>")
            else:
                probe_letter = reverse_mapping[textlabel]
                data = data.replace(
                    f">{textlabel}</tspan>", f"> {probe_letter}</tspan>"
                )
        return data

    def resolve_current_probe_hole_assignments(self):
        "Resolve conflicts, such as multiple probes assigned to the same hole"

        for probe, hole in dict(self.previous_probe_hole_assignments).items():
            if (
                len(
                    [
                        t
                        for t in self.previous_probe_hole_assignments.values()
                        if t == hole
                    ]
                )
                > 1
            ):  # probe was previously un-assigned from a hole that another probe was also assigned
                if (
                    self.current_probe_hole_assignments[probe] is None
                    and hole not in self.current_probe_hole_assignments.values()
                ):
                    # restore previously assigned hole, now that it's unoccupied
                    self.current_probe_hole_assignments[probe] = hole
                    # print(f"Restored previous target for {probe} to {hole}")

        for probe, hole in dict(self.current_probe_hole_assignments).items():
            if (
                len(
                    [
                        t
                        for t in self.current_probe_hole_assignments.values()
                        if t == hole
                    ]
                )
                > 1
            ):  # probe is assigned a hole that another probe is also assigned to
                if self.previous_probe_hole_assignments[probe] == hole:
                    # this probe was previously assigned to this hole, so it's probably
                    # getting 'overwritten' by a new probe assignment, which will take
                    # precedence
                    self.current_probe_hole_assignments[probe] = None
                    # print(f"Probe {probe} was previously assigned to hole {hole}, but is now being overwritten by another probe assignment. Probe {probe} will be removed from the implant.")

            # for newly-updated probes, store their target hole in memory
            if self.current_probe_hole_assignments[probe]:
                self.previous_probe_hole_assignments[
                    probe
                ] = self.current_probe_hole_assignments[probe]


class TS5DrawingSVG(DrawingSVG):
    """Functions for controlling and altering graphic representation of ProbeGroups on implant image,
    but not functions for displaying it."""

    svg_path: pathlib.Path = pathlib.Path(__file__).resolve().parent / "DR1_no_shading.svg"
    ".svg of first production DR implant, known as DR1, TS-5, 2002, with labels for each hole that designate a probe (A1, B2, etc.)"
    implant: ImplantHoles = TS5()
    probes: Type[ProbeGroup] = TS5ProbeGroup

    
class TempletonDrawingSVGProbeColormap(DrawingSVG):
    """Functions for controlling and altering graphic representation of ProbeGroups on implant image,
    but not functions for displaying it."""
    svg_path: pathlib.Path = pathlib.Path(__file__).resolve().parent / "Templeton_probes.svg"
    implant: ImplantHoles = Templeton()
    probes: Type[ProbeGroup] = TempletonProbeGroup
    
    
class TempletonDrawingSVGComboColormap(DrawingSVG):
    """Functions for controlling and altering graphic representation of ProbeGroups on implant image,
    but not functions for displaying it."""
    svg_path: pathlib.Path = pathlib.Path(__file__).resolve().parent / "Templeton_combos.svg"
    implant: ImplantHoles = Templeton()
    probes: Type[ProbeGroup] = TempletonProbeGroup
    
    
class ProbeTargetInsertionRecordWidget(ipw.HBox):
    "Displays implant, configurable probe-hole assignments, and buttons for interaction"

    def __init__(
        self, targets: ProbeGroup, implant_drawing=TS5DrawingSVG, current_insertion_group: Type[ProbeGroup] = ProbeInsertionsTS5, *args, **kwargs
    ):
        "Requires targets and a drawing"

        self.initial_targets: dict[str, str | None] = dict(targets)
        self.probe_letters: list[str] = list(targets.keys())

        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

        self.from_record: bool = (
            targets.from_record if hasattr(targets, "from_record") else False
        )

        # interactive display of implant and probe-hole assignments ---------------------------- #

        self.current_insertions: ProbeGroup = current_insertion_group(
            dict(targets), notes=targets.notes
        )
        "Current probe-hole assignments that can be updated interactively, saved to disk"
        self.implant_drawing = implant_drawing(self.current_insertions)
        "Holds current probe-hole assignments in ProbeGroups and modifies drawing content accordingly"

        if isinstance(
            self.implant_drawing.drawing_with_current_probe_hole_assignments, str
        ):
            self.update_current_probe_hole_assignment_display = (
                self.update_probe_hole_assignments_display_from_html
            )

        self.probe_hole_sliders = [
            ipw.SelectionSlider(
                options=["none", *self.implant_drawing.implant.hole_labels],
                value=self.current_insertions[probe] or "none",
                description=f"probe {probe}",
                continuous_update=True,
                orientation="horizontal",
                readout=True,
            )
            for probe in self.probe_letters
        ]
        "Set and display probe-hole assignments for each probe"

        link_args = dict(zip(self.probe_letters, self.probe_hole_sliders))

        def interactive_probe_hole_assignment(**kwargs):
            "Update probe-hole assignments when sliders are changed"
            for probe, hole in kwargs.items():
                self.current_insertions[probe] = hole
            self.update_current_probe_hole_assignment_display()

        # -------------------------------------------------------------------------------------- #
        self.interactive_implant_display = ipw.interactive_output(
            f=interactive_probe_hole_assignment,
            controls=link_args,
        )
        # -------------------------------------------------------------------------------------- #

        # additional ui elements --------------------------------------------------------------- #
        self.note_entry_boxes = [
            ipw.Text(
                value=self.current_insertions.probe[probe].notes,
                placeholder=f"Add notes for probe {probe}",
                continuous_update=True,
            )
            for probe in self.probe_letters
        ]
        "Text entry box for notes for each probe"

        self.slider_ui = (
            ipw.VBox([*self.probe_hole_sliders])
            if (self.probe_hole_sliders[0].orientation == "horizontal")
            else ipw.HBox([*self.probe_hole_sliders])
        )
        self.notes_ui = ipw.VBox([*self.note_entry_boxes])
        # -------------------------------------------------------------------------------------- #
        self.slider_notes_ui = ipw.HBox([self.slider_ui, self.notes_ui])
        # -------------------------------------------------------------------------------------- #

        self.save_button = ipw.Button(description="Save", button_style="success")
        self.clear_button = ipw.Button(description="Clear", button_style="warning")
        self.reload_button = ipw.Button(
            description="Reload targets", button_style="info"
        )
        self.save_button.on_click(functools.partial(self.save_button_clicked, self))
        self.clear_button.on_click(functools.partial(self.clear_button_clicked, self))
        self.reload_button.on_click(functools.partial(self.reload_button_clicked, self))
        # -------------------------------------------------------------------------------------- #
        self.button_ui = ipw.HBox(
            [self.clear_button, self.reload_button, self.save_button]
        )
        # -------------------------------------------------------------------------------------- #

        self.output = ipw.Output()
        "Console for displaying messages"

        self.console_clear()

        left_box = self.interactive_implant_display
        right_box = ipw.VBox([self.slider_notes_ui, self.button_ui, self.output])
        super().__init__(
            [
                left_box,
                right_box,
            ]
        )
        "Feed all UI elements into superclass widget"

        self.layout = ipw.Layout(width="100%")

        # UI adjustments
        inputs = [
            *self.button_ui.children,
            *self.probe_hole_sliders,
            *self.note_entry_boxes,
        ]
        if self.from_record:
            self.console_print(f"Insertion record loaded (read-only).")
            for input in inputs:
                input.disabled = True
                if isinstance(input, ipw.Button):
                    input.button_style = ""

    # end of init - widget returned/displayed ----------------------------------------------- #

    @property
    def probe_hole_assignments_display_handle(self):
        if not hasattr(self, "_probe_hole_assignments_display"):
            self._probe_hole_assignments_display = IPython.display.DisplayHandle()
        return self._probe_hole_assignments_display

    def update_probe_hole_assignments_display_from_html(self):
        self.probe_hole_assignments_display_handle.update(
            ipw.HTML(
                self.implant_drawing.drawing_with_current_probe_hole_assignments,
                layout=ipw.Layout(align_content="center", object_fit="scale-down"),
                # layout not working
            )
        )

    def console_print(self, msg: str):
        with self.output:
            print(f"{datetime.datetime.now().strftime('%H:%M:%S')} {msg}")

    def console_clear(self):
        msg = " " * 30
        with self.output:
            print(f"{msg}")

    def save_button_clicked(self, *args, **kwargs):
        day = self.day if hasattr(self, "day") else None
            
        #! notes are not being transferred to Probe class via note_entry_boxes:
        # will manually update notes prior to saving as a temp fix
        for probe, text in zip(self.current_insertions._probes, self.note_entry_boxes):
            probe.notes = text.value or None
        # print([text.value for text in self.note_entry_boxes])
        # print([text.notes for text in self.current_insertions._probes])
        self.current_insertions.save(day=day)
        self.console_print("Insertions saved.")

    def clear_button_clicked(self, *args, **kwargs):
        for slider in self.probe_hole_sliders:
            slider.value = "none"
        self.console_clear()

    def reload_button_clicked(self, *args, **kwargs):
        for probe, slider in zip(self.probe_letters, self.probe_hole_sliders):
            hole = self.initial_targets[probe]
            if hole is not None:
                slider.value = hole
            else:
                slider.value = "none"
        self.console_print("Targets reloaded.")


class DRWeeklyTargets(ipw.Tab):
    def __init__(self, week: Optional[int] = None):

        super().__init__()

        days = (1, 2, 3, 4)
        ui_each_day = []
        for day in days:

            # try to get previously-saved insertions for this day
            try:
                insertions = ProbeInsertionsTS5(day=day)
            except FileNotFoundError:
                insertions = None

            ui_each_day.append(
                ProbeTargetInsertionRecordWidget(
                    targets=insertions or ProbeTargetsFromPlanTS5(day=day, week=week),
                    implant_drawing=TS5DrawingSVG,
                    day=day,
                )
            )
        self.children = ui_each_day

        # setting titles is different between ipywidgets 8.x and 7.x
        # (7.x is latest v. compatible w/VSCode Oct'22)
        tab_titles = [f"Day {day}" for day in days]
        try:
            # ipw 7.x
            # map(self.set_title, enumerate(tab_titles))
            for tab, day in enumerate(days):
                self.set_title(tab, f"Day {day}")
        except:
            # ipw 8.x
            self.titles = tab_titles

        self.layout = ipw.Layout(align_content="center", height="auto", width="auto")


class DRWeeklyTargetsViewOnly(ipw.Tab):
    def __init__(self, week=None):
        "Display-only weekly targets - defaults to current week from plan"
        super().__init__()

        days = (1, 2, 3, 4)
        ui_each_day = []
        for day in days:
            ui_each_day.append(
                ipw.HTML(
                    TS5DrawingSVG(
                        ProbeTargetsFromPlanTS5(day=day, week=week),
                    ).drawing_with_current_probe_hole_assignments
                )
            )
        self.children = ui_each_day

        # setting titles is different between ipywidgets 8.x and 7.x
        # (7.x is latest v. compatible w/VSCode Oct'22)
        tab_titles = [f"Day {day}" for day in days]
        try:
            # ipw 7.x
            # map(self.set_title, enumerate(tab_titles))
            for tab, day in enumerate(days):
                self.set_title(tab, f"Day {day}")
        except:
            # ipw 8.x
            self.titles = tab_titles

        self.layout = ipw.Layout(align_content="center", height="auto", width="auto")


class CurrentWeek:
    "The current week at runtime: displayed so user can check if GUI needs refreshing"
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    friday = monday + datetime.timedelta(days=4)
    DR_plan_week = ProbeTargetsFromPlanTS5.get_plan_week()

    def __str__(self) -> str:
        return (
            f"Week {self.DR_plan_week}: "
            f"{self.monday.strftime('%d')}-"
            f"{self.friday.strftime('%d %b')}"
        )

    @classmethod
    def display(cls):
        return IPython.display.display(ipw.HTML(f"<h3>{cls()}</h3>"))
