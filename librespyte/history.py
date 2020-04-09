#!/usr/bin/env python3
"""Main view of respyte"""
from os import makedirs, path
import json
from asciimatics.widgets import Button, Divider, ListBox, Frame, Layout
from asciimatics.exceptions import NextScene

CONFIG_DIRECTORY = path.expanduser(path.join("~", ".config", "respyte"))
HISTORY_FILE = path.join(CONFIG_DIRECTORY, "history.json")
SCRATCH_FILE = path.join(CONFIG_DIRECTORY, "scratch.json")

class HistoryView(Frame):
    """This is the rest composition menu"""
    def __init__(self, screen, parsed_args):
        super(HistoryView, self).__init__(screen,
                                          screen.height,
                                          screen.width,
                                          hover_focus=True,
                                          can_scroll=False,
                                          title="Respyte")

        theme = parsed_args.color_scheme
        self.set_theme(theme)
        # Create the form for displaying the list of contacts.
        history_layout = Layout([1])
        self.add_layout(history_layout)
        self.data['history'] = 0
        history_list = ListBox(screen.height - 5,
                               self._history(), label="History",
                               name="history")
        history_layout.add_widget(history_list, 0)

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
                    {"method": "GET", "url": '', "headers": '', 'data': ''}
                ))
        with open(HISTORY_FILE, 'r') as history_file:
            lines = history_file.readlines()
            options = []
            index = 0
            for line in lines:
                if line.strip():
                    options.append((json.dumps(json.loads(line)), index))
                index += 1
            return options

    @staticmethod
    def _cancel():
        raise NextScene("Main")

    def _select(self):
        self.save()
        with open(SCRATCH_FILE, 'w') as scratch_file:
            scratch_file.write(json.dumps({"history":self.data['history']}))
        raise NextScene("Main")
