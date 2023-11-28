from __future__ import annotations

import datetime
import functools
import json
import pathlib

import IPython.display
import ipywidgets as ipw
import npc_session
from typing_extensions import Self

import np_probe_targets.insertions
import np_probe_targets.shields
import np_probe_targets.types


class InsertionWidget(ipw.HBox):
    """Displays implant drawing, configurable probe-hole assignments, and buttons for interaction"""

    @classmethod
    def from_record(cls, json_path: pathlib.Path, **kwargs) -> Self:
        """Load widget from an existing insertion record."""
        return cls(
            insertion=np_probe_targets.insertions.InsertionRecord.from_json(
                json.loads(json_path.read_text())
            ),
            save_path=json_path,
            **kwargs,
        )

    def __init__(
        self,
        insertion: np_probe_targets.types.Insertion,
        save_path: str | pathlib.Path,
        read_only: bool = False,
        **hbox_kwargs,
    ) -> None:
        for k, v in hbox_kwargs.items():
            setattr(self, k, v)

        self.save_path = pathlib.Path(save_path)
        self.insertion = insertion
        self.initial_targets = dict(insertion.probes)
        self.probe_letters = sorted(self.insertion.probes.keys())

        self.probe_hole_sliders = [
            ipw.SelectionSlider(
                options=["none", *self.insertion.shield.labels],
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
            for probe, hole in kwargs.items():
                if hole == "none":
                    hole = None
                self.insertion.probes[probe] = hole
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

        self.save_path.write_text(json.dumps(self.insertion.to_json(), indent=2))
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
    save_path: pathlib.Path,
) -> InsertionWidget:
    return InsertionWidget(
        insertion=np_probe_targets.insertions.InsertionRecord(
            shield=np_probe_targets.shields.get_shield(shield_name),
            session=session,
            experiment_day=experiment_day,
            probes=None,
            notes=None,
        ),
        save_path=save_path,
    )
