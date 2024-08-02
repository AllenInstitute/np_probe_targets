"""
# Get an implant with suggested targets from a dict
>>> shield = npc_shields.shields.get_shield('2002')
>>> suggested_targets = npc_shields.insertions.InsertionRecord(
...     shield=shield,
...     probes={
...         'A': 'A1',
...         'B': None,
...         'C': 'C1',
...         'D': 'D2',
...         'E': 'F1',
...         'F': 'F2',
...     },
...     session='366122_20231201',
...     experiment_day=1,
... )
>>> w = InsertionWidget(
...     insertion=suggested_targets,
...     save_paths='example-record.json'
... ) # doctest: +SKIP

# # Get an implant with suggested targets from a previously-saved record
# >>> suggested_targets = InsertionWidget.from_record(pathlib.Path('examples/example-record.json'))
"""
from __future__ import annotations

import datetime
import functools
import json
import pathlib
from collections.abc import Iterable
from typing import Any

import IPython.display
import ipywidgets as ipw
import npc_session
import pydantic
from typing_extensions import Self

import npc_shields.injections
import npc_shields.insertions
import npc_shields.shields
import npc_shields.types


class InsertionWidget(ipw.HBox):
    """Displays implant drawing, configurable probe-hole assignments, and buttons for interaction"""

    @classmethod
    def from_record(cls, json_path: pathlib.Path, **kwargs) -> Self:
        """Load widget from an existing insertion record."""
        return cls(
            insertion=npc_shields.insertions.InsertionRecord.from_json(
                json.loads(json_path.read_text())
            ),
            save_paths=json_path,
            **kwargs,
        )

    def __init__(
        self,
        insertion: npc_shields.types.Insertion,
        save_paths: str | pathlib.Path | Iterable[pathlib.Path],
        read_only: bool = False,
        **hbox_kwargs,
    ) -> None:
        for k, v in hbox_kwargs.items():
            setattr(self, k, v)

        if isinstance(save_paths, str):
            save_paths = pathlib.Path(save_paths)
        if not isinstance(save_paths, Iterable):
            save_paths = (save_paths,)
        self.save_paths: Iterable[pathlib.Path] = save_paths  # type: ignore [assignment]

        self.insertion = insertion
        self.initial_targets = dict(insertion.probes)
        self.probe_letters = sorted(self.insertion.probes.keys())

        self.probe_hole_sliders = [
            ipw.SelectionSlider(
                options=["none", *self.insertion.shield.holes.keys()],
                value=self.insertion.probes[probe] or "none",
                description=f"probe {probe}",
                continuous_update=True,
                orientation="horizontal",
                readout=True,
            )
            for probe in self.probe_letters
        ]

        def update_insertions(**kwargs) -> None:
            "Update probe-hole assignments when sliders are changed"
            assignments = {k: v if v != "none" else None for k, v in kwargs.items()}
            self.insertion.probes.update(assignments)
            self.update_display()

        self.interactive_insertion = ipw.interactive_output(
            f=update_insertions,
            controls=dict(zip(self.probe_letters, self.probe_hole_sliders)),
        )

        # additional ui elements --------------------------------------------------------------- #
        self.note_entry_boxes = [
            ipw.Text(
                value=self.insertion.notes[probe],
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

        left_box = self.interactive_insertion
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
        if read_only:
            self.console_print("Insertion record loaded (read-only).")
            for input in inputs:
                input.disabled = True
                if isinstance(input, ipw.Button):
                    input.button_style = ""

    # end of init - widget returned/displayed ----------------------------------------------- #

    @property
    def probe_hole_assignments_display_handle(self) -> IPython.display.DisplayHandle:
        if not hasattr(self, "_probe_hole_assignments_display"):
            self._probe_hole_assignments_display = IPython.display.DisplayHandle()
        return self._probe_hole_assignments_display

    def update_display(self) -> None:
        self.probe_hole_assignments_display_handle.display(
            ipw.HTML(
                self.insertion.to_svg(),
                layout=ipw.Layout(align_content="center", object_fit="scale-down"),
                # layout not working
            )
        )

    def console_print(self, msg: str) -> None:
        with self.output:
            print(f"{datetime.datetime.now().strftime('%H:%M:%S')} {msg}")

    def console_clear(self) -> None:
        msg = " " * 30
        with self.output:
            print(f"{msg}")

    def save_button_clicked(self, *args, **kwargs) -> None:
        for probe, text in zip(self.insertion.probes, self.note_entry_boxes):
            self.insertion.notes[probe] = text.value or None
        text = json.dumps(self.insertion.to_json(), indent=2)
        for path in self.save_paths:
            path.write_text(text)
        self.console_print("Insertions saved.")

    def clear_button_clicked(self, *args, **kwargs) -> None:
        for slider in self.probe_hole_sliders:
            slider.value = "none"
        self.console_clear()

    def reload_button_clicked(self, *args, **kwargs) -> None:
        for probe, slider in zip(self.probe_letters, self.probe_hole_sliders):
            hole = self.initial_targets[probe]
            if hole is not None:
                slider.value = hole
            else:
                slider.value = "none"
        self.console_print("Targets reloaded.")


def get_insertion_widget(
    shield_name: str,
    session: str | npc_session.SessionRecord,
    experiment_day: int,
    save_paths: str | pathlib.Path | Iterable[pathlib.Path],
) -> InsertionWidget:
    # """

    # >>> w = get_insertion_widget(
    # ...     shield_name='2002',
    # ...     session='366122_20231201',
    # ...     experiment_day=1,
    # ...     save_paths=pathlib.Path('examples/example-record.json'),
    # ... )
    # """
    return InsertionWidget(
        insertion=npc_shields.insertions.InsertionRecord(
            shield=npc_shields.shields.get_shield(shield_name),
            session=session,
            experiment_day=experiment_day,
            probes=None,
            notes=None,
        ),
        save_paths=save_paths,
    )


class InjectionWidget(ipw.VBox):
    """
    A widget for a single session, allowing one or more injections to be added.
    """

    injections: set[npc_shields.types.Injection]
    gridspec_kwargs: dict[str, Any]
    shield: npc_shields.types.Shield | None

    def __init__(
        self,
        session: str | npc_session.SessionRecord,
        injection_day_index: int,
        save_paths: str | pathlib.Path | Iterable[pathlib.Path],
        shield_name: str | None = None,
        injection_cls: type[pydantic.BaseModel] = npc_shields.injections.Injection,
        **vbox_kwargs,
    ) -> None:
        self.session = session
        self.injection_day_index = injection_day_index
        self.save_paths = save_paths  # type: ignore [assignment]
        if shield_name is not None:
            self.shield = npc_shields.shields.get_shield(shield_name)
        else:
            self.shield = None
        self.injection_cls = injection_cls
        self.injections = self.load_existing_injections()

        def get_hint(name, field) -> str:
            if name == "start_time":
                return "[required] YYYY-MM-DD HH:MM"
            return f"{'[required]' if field.is_required() else ''}"

        self.text_entry_boxes = {
            name: ipw.Text(
                description=name,
                placeholder=get_hint(name, field),
                tooltip=field.description or name,
                continuous_update=True,
                layout=ipw.Layout(width="100%"),
            )
            for name, field in self.injection_cls.model_fields.items()
            if name not in ("shield")
        }
        self._apply_default_injection_values()
        self._apply_previous_injection_values()
        self.text_entry_grid = ipw.GridBox(
            list(self.text_entry_boxes.values()),
        )
        hbox_elements = [self.text_entry_grid]
        if self.shield:
            hbox_elements.append(
                ipw.HTML(
                    self.shield.drawing_svg.read_text(),
                    layout=ipw.Layout(align_content="center", object_fit="scale-down"),
                    # layout not working
                )
            )
        hbox = ipw.HBox(hbox_elements)
        self.vbox_kwargs = vbox_kwargs

        self.add_injection_button = ipw.Button(
            description="Add this injection",
            button_style="success",
            layout=ipw.Layout(width="30%"),
            tooltip="Append the current set of parameters as a unique injection for this session",
        )
        self.add_injection_button.on_click(lambda _: self.add_injection())

        self.add_reset_button = ipw.Button(
            description="Reset form",
            button_style="warning",
            layout=ipw.Layout(width="30%"),
            tooltip="Clear all data entered in fields and reset to default values",
        )
        self.add_reset_button.on_click(lambda _: self._apply_default_injection_values())

        self.console = ipw.Output()

        if self.injections:
            with self.console:
                print(
                    f"Loaded existing injections [total: {len(self.injections)} injections]"
                )

        super().__init__(
            [hbox, self.add_injection_button, self.add_reset_button, self.console],
            **vbox_kwargs,
        )

    @property
    def save_paths(self) -> tuple[pathlib.Path, ...]:
        return self._save_paths

    @save_paths.setter
    def save_paths(self, paths: str | pathlib.Path | Iterable[pathlib.Path]) -> None:
        if isinstance(paths, str):
            paths = (pathlib.Path(paths),)
        if not isinstance(paths, Iterable):
            paths = (paths,)
        paths = (pathlib.Path(path) for path in paths)
        self._save_paths = tuple(
            path / "injections.json" if path.is_dir() else path for path in paths
        )

    def _apply_default_injection_values(self) -> None:
        for name, field in self.injection_cls.model_fields.items():
            if name in ("shield"):
                continue
            if "PydanticUndefined" in field.default.__class__.__name__:
                self.text_entry_boxes[name].value = ""
            elif field.default is None:
                self.text_entry_boxes[name].value = ""
            else:
                self.text_entry_boxes[name].value = str(getattr(field, "default", ""))

    def _apply_previous_injection_values(self) -> None:
        if not self.injections:
            return None
        latest_injection: npc_shields.types.Injection = max(
            self.injections, key=lambda x: x.start_time
        )
        latest_injection_data = latest_injection.to_json() if latest_injection else {}
        for name in self.text_entry_boxes:
            value = latest_injection_data.get(name)
            if value is not None:
                self.text_entry_boxes[name].value = str(value)

    def add_injection(self) -> None:
        try:
            injection = self.injection_cls(
                shield=self.shield,
                **{
                    name: box.value if box.value != "" else None
                    for name, box in self.text_entry_boxes.items()
                },
            )
        except pydantic.ValidationError as e:
            with self.console:
                self.console.clear_output()
                print(f"Error: {e!r}")
            return
        current_num_injections = len(self.injections)
        self.injections.add(injection)  # type: ignore [arg-type]
        self.write_record()
        with self.console:
            self.console.clear_output()
            if current_num_injections == len(self.injections):
                print(
                    f"Injection already exists for these parameters [total: {len(self.injections)} injections]"
                )
            else:
                print(f"Added injection [new total: {len(self.injections)} injections]")

    def load_existing_injections(self) -> set[npc_shields.types.Injection]:
        existing = set()
        for path in self.save_paths:
            if path.exists():
                data = json.loads(path.read_text())
                for injection in data["injections"]:
                    injection["shield"] = npc_shields.shields.get_shield(
                        injection["shield"]["name"]
                    )
                    existing.add(self.injection_cls(**injection))
        return existing  # type: ignore [return-value]

    def create_record(self) -> npc_shields.injections.InjectionRecord:
        return npc_shields.injections.InjectionRecord(
            injections=self.injections,
            session=self.session,
            injection_day_index=self.injection_day_index,
        )

    def write_record(self) -> None:
        record = self.create_record()
        for path in self.save_paths:
            path.write_text(json.dumps(record.to_json(), indent=4))


if __name__ == "__main__":
    import doctest

    doctest.testmod(optionflags=doctest.FAIL_FAST)
