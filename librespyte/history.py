#!/usr/bin/env python3
"""Main view of respyte"""
from os import makedirs, path
import json
from yaml import safe_load, dump
from asciimatics.widgets import Button, Divider, ListBox, Frame, Layout
from asciimatics.exceptions import NextScene
from librespyte.pager import Pager

CONFIG_DIRECTORY = path.expanduser(path.join("~", ".config", "respyte"))
HISTORY_FILE = path.join(CONFIG_DIRECTORY, "history.json")
SCRATCH_FILE = path.join(CONFIG_DIRECTORY, "scratch.json")

class HistoryView(Frame):
    """This is the rest composition menu"""
    def __init__(self, screen, parsed_args):
        super(HistoryView, self).__init__(screen,
                                          screen.height,
                                          screen.width,
                                          on_load=self._update_preview,
                                          hover_focus=True,
                                          can_scroll=False,
                                          title="Respyte")

        theme = parsed_args.color_scheme
        self.set_theme(theme)
        # Create the form for displaying the list of contacts.
        history_layout = Layout([1])
        self.add_layout(history_layout)
        self.data['history'] = 0
        self.preview_box = Pager(
            screen.height // 2,
            label="Preview body",
            name="preview",
            line_wrap=True,
            as_string=True,
            tab_stop=False,
        )
        self.history_list = ListBox(
            (screen.height//2) - 4,
            self._history(), label="History",
            on_change=self._update_preview,
            on_select=self._update_preview,
            name="history"
        )
        self._update_preview()
        history_layout.add_widget(self.history_list, 0)
        preview_layout = Layout([1])
        self.add_layout(preview_layout)
        preview_layout.add_widget(self.preview_box, 0)
        button_layout = Layout([1, 1, 1])
        self.add_layout(button_layout)
        button_layout.add_widget(Divider())
        button_layout.add_widget(Divider(), 1)
        button_layout.add_widget(Divider(), 2)
        button_layout.add_widget(Button("Select", self._select), 0)
        button_layout.add_widget(Button("Cancel", self._cancel), 2)

        self.fix()

    def _history(self):
        """Show history"""
        if not path.isfile(HISTORY_FILE):
            makedirs(CONFIG_DIRECTORY, exist_ok=True)
            with open(HISTORY_FILE, 'w') as history_file:
                history_file.write(json.dumps(
                    {'history': []}
                ))
        options = []
        with open(HISTORY_FILE, 'r') as history_file:
            lines = json.loads(history_file.read())['history']
            index = 0
            for line in lines:
                options.append((json.dumps(line), index))
                index += 1
        return options

    def _update_preview(self):
        try:
            options = self._history()
            self.history_list.options = self._history()
            self.screen.refresh()
            self.preview_box.value = dump(safe_load(str(options[self.history_list.value][0])))
        except TypeError:
            self.preview_box.value = ""
        except IndexError:
            self.preview_box.value = "No preview available"

    @staticmethod
    def _cancel():
        raise NextScene("Main")

    def _select(self):
        self.save()
        with open(SCRATCH_FILE, 'w') as scratch_file:
            scratch_file.write(json.dumps({"history":self.data['history']}))
        raise NextScene("Main")
