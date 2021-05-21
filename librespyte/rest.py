#!/usr/bin/env python3
"""Main view of respyte"""
from os import path, remove
import json
import re
import yaml
import requests
import urllib3
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Divider, DropdownList, Frame, Layout, Text, \
    TextBox, VerticalDivider, PopUpDialog
from asciimatics.exceptions import  StopApplication, NextScene
from librespyte.pager import Pager
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_DIRECTORY = path.expanduser(path.join("~", ".config", "respyte"))
HISTORY_FILE = path.join(CONFIG_DIRECTORY, "history.json")
SCRATCH_FILE = path.join(CONFIG_DIRECTORY, "scratch.json")
HELP = """
Welcome to Respyte help:
Use tab to navigate between inputs.
The First input is the HTTP method, listed as a dropdown
The second is a url text field, if the url does not validate, it will appear in an error highlight
The next two input fields are Headers, and Body Params, both of which are parsed as YAML, so you may input YAML or json in those inputs.
The next field is the Response body it is a scrollabled view interactable like a less pager (j/k/u/d/G/g).

The Bottom Row buttons are `Send it` `History` and `Quit`
Send it: Send the HTTP request to the endpoint utilizing the given HTTP method with the headers and body parameters
History: View the History of your requests
Quit: Exit Respyte

You will Also note that they have corresponding keys attached to them, you may press those keys at any point in time to execute that command.
"""

def validate(test_url):
    """ensures url is valid"""
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, test_url) is not None

class RestView(Frame):
    """This is the rest composition menu"""
    def __init__(self, screen, parsed_args):
        super(RestView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._populate,
                                       hover_focus=True,
                                       can_scroll=False,
                                       title="Respyte")

        self.theme = parsed_args.color_scheme
        self.set_theme(self.theme)
        url_layout = Layout([10, 1, 100])
        self.add_layout(url_layout)
        self.screen_holder = screen
        self.method = DropdownList(
            [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"),
             ("PATCH", "PATCH"), ("DELETE", "DELETE")],
            name="method")
        url_layout.add_widget(self.method, 0)
        url_layout.add_widget(VerticalDivider(), 1)
        self.url = Text(label="Url: ",
                        validator=validate,
                        name="url")
        url_layout.add_widget(self.url, 2)

        url_layout.add_widget(Divider())
        url_layout.add_widget(Divider(), 1)
        url_layout.add_widget(Divider(), 2)
        req_layout = Layout([20, 1, 50], fill_frame=True)
        self.add_layout(req_layout)
        self.request = TextBox(screen.height // 4 * 3 - 7,
                               label="Body Params",
                               name="req_params",
                               line_wrap=True,
                               as_string=True
                               )
        self.req_headers = TextBox(screen.height // 4,
                                   label="Headers",
                                   name="req_headers",
                                   line_wrap=True,
                                   as_string=True
                                   )
        req_layout.add_widget(self.req_headers, 0)
        req_layout.add_widget(Divider(), 0)
        req_layout.add_widget(self.request, 0)

        req_layout.add_widget(VerticalDivider(), 1)
        self.resp_headers = TextBox(screen.height // 4,
                                    label="Response Headers",
                                    name="resp_headers",
                                    line_wrap=True,
                                    as_string=True,
                                    readonly=True,
                                    tab_stop=False,
                                    )
        req_layout.add_widget(self.resp_headers, 2)
        req_layout.add_widget(Divider(), 2)
        self.response = Pager(screen.height // 4 * 3 - 7,
                              label="Response body",
                              name="response",
                              line_wrap=True,
                              as_string=True,
                              )
        req_layout.add_widget(self.response, 2)

        button_layout = Layout([1, 1, 1])
        self.add_layout(button_layout)
        button_layout.add_widget(Divider())
        button_layout.add_widget(Divider(), 1)
        button_layout.add_widget(Divider(), 2)
        button_layout.add_widget(Button("Send it <F3>", self._send), 0)
        button_layout.add_widget(Button("History <F2>", self._history), 1)
        button_layout.add_widget(Button("Quit <ESC>", self._quit), 2)
        self._populate()
        self.fix()

    def _history(self):
        """Show history"""
        raise NextScene("History")

    def _open_help(self):
        self._scene.add_effect(
            PopUpDialog(
                self._screen,
                HELP,
                ["Ok"],
                # has_shadow=True,
                theme="default"
            )
        )

    def _populate(self):
        """populate information"""
        self.save()
        if path.isfile(SCRATCH_FILE) and path.isfile(HISTORY_FILE):
            with open(SCRATCH_FILE, 'r') as scratch_file:
                selection = json.loads(scratch_file.read())["history"]
            remove(SCRATCH_FILE)
            with open(HISTORY_FILE, 'r') as history_file:
                json_obj = json.loads(history_file.read())['history'][selection]
                self.request.value = yaml.dump(json_obj['data'])
                self.req_headers.value = yaml.dump(json_obj['headers'])
                self.url.value = json_obj['url']
                self.method.value = json_obj['method']
        self.screen.refresh()
        self.fix()

    @staticmethod
    def _quit():
        history = []
        with open(HISTORY_FILE, 'r') as history_file:
            for line in history_file.readlines():
                if line.strip():
                    history.append(line)
        history = list(set(history))
        with open(HISTORY_FILE, 'w') as history_file:
            for line in history:
                history_file.write('\n')
                history_file.write(line)

        raise StopApplication("User pressed quit")

    def _send(self):
        try:
            self.save()
            data = yaml.safe_load(self.data['req_params']) if self.data['req_params'] else {}
            self.request.value = yaml.dump(data, indent=2, sort_keys=True)
            headers = yaml.safe_load(self.data['req_headers']) if self.data['req_headers'] else {}
            if 'Authorization' in headers and len(headers['Authorization'].split('.')) > 1:
                try:
                    headers['Authorization'] = custom_auth(headers['Authorization'],
                                                           self.data['url'],
                                                           data,
                                                           headers,
                                                           )
                except ImportError:
                    pass
            # self.req_headers.value = json.dumps(headers, indent=2, sort_keys=True)
            # req = requests.get(self.data['url'], data=data)
            method = self.data['method'] if self.data['method'] else 'GET'
            history = {"method": method, "url": self.data['url'],
                       "data": data, "headers": headers}
            req = requests.request(method,
                                   self.data['url'],
                                   data=data,
                                   headers=headers,
                                   verify=False
                                   )
            self.resp_headers.value = yaml.dump(dict(req.headers), allow_unicode=True)
            try:
                self.response.value = yaml.dump(req.json(), allow_unicode=True)
                with open(HISTORY_FILE, 'r') as history_file:
                    current_history = json.loads(history_file.read())
                current_history['history'].append(history)
                with open(HISTORY_FILE, "w") as history_file:
                    json.dump(current_history, history_file)

            except json.JSONDecodeError:
                self.response.value = req.text
            self.screen.refresh()
        except Exception as err: # pylint: disable=broad-except
            self.scene.add_effect(PopUpDialog(self.screen, str(err), ["Ok"]))

    def process_event(self, event):
        # Rebase any mouse events into Frame coordinates now.
        old_event = event
        event = self.rebase_event(event)

        # Claim the input focus if a mouse clicked on this Frame.
        claimed_focus = False
        if isinstance(event, MouseEvent) and event.buttons > 0:
            if (0 <= event.x < self._canvas.width and
                    0 <= event.y < self._canvas.height):
                self._scene.remove_effect(self)
                self._scene.add_effect(self, reset=False)
                if not self._has_focus and self._focus < len(self._layouts):
                    self._layouts[self._focus].focus()
                self._has_focus = claimed_focus = True
            else:
                if self._has_focus and self._focus < len(self._layouts):
                    self._layouts[self._focus].blur()
                self._has_focus = False
        elif isinstance(event, KeyboardEvent):
            # TODO: Should have Desktop Manager handling this - wait for v2.0
            # By this stage, if we're processing keys, we have the focus.
            if not self._has_focus and self._focus < len(self._layouts):
                self._layouts[self._focus].focus()
            self._has_focus = True

        # No need to do anything if this Frame has no Layouts - and hence no
        # widgets.  Swallow all Keyboard events while we have focus.
        #
        # Also don't bother trying to process widgets if there is no defined
        # focus.  This means there is no enabled widget in the Frame.
        if (self._focus < 0 or self._focus >= len(self._layouts) or
                not self._layouts):
            if event is not None and isinstance(event, KeyboardEvent):
                return None
            # Don't allow events to bubble down if this window owns the Screen - as already
            # calculated when taking te focus - or is modal.
            return None if claimed_focus or self._is_modal else old_event

        # Give the current widget in focus first chance to process the event.
        event = self._layouts[self._focus].process_event(event, self._hover_focus)

        # If the underlying widgets did not process the event, try processing
        # it now.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                function_key_map = {
                    Screen.KEY_ESCAPE: self._quit,
                    Screen.KEY_F1: self._open_help,
                    Screen.KEY_F2: self._history,
                    Screen.KEY_F3: self._send,
                }
                if event.key_code == Screen.KEY_TAB:
                    # Move on to next widget.
                    self._layouts[self._focus].blur()
                    self._find_next_tab_stop(1)
                    self._layouts[self._focus].focus(force_first=True)
                    old_event = None
                elif event.key_code == Screen.KEY_BACK_TAB:
                    # Move on to previous widget.
                    self._layouts[self._focus].blur()
                    self._find_next_tab_stop(-1)
                    self._layouts[self._focus].focus(force_last=True)
                    old_event = None
                elif event.key_code == Screen.KEY_DOWN:
                    # Move on to nearest vertical widget in the next Layout
                    self._switch_to_nearest_vertical_widget(1)
                    old_event = None
                elif event.key_code == Screen.KEY_UP:
                    # Move on to nearest vertical widget in the next Layout
                    self._switch_to_nearest_vertical_widget(-1)
                    old_event = None
                elif event.key_code in function_key_map.keys():
                    function_key_map[event.key_code]()
            elif isinstance(event, MouseEvent):
                # Give layouts/widgets first dibs on the mouse message.
                for layout in self._layouts:
                    if layout.process_event(event, self._hover_focus) is None:
                        return None

                # If no joy, check whether the scroll bar was clicked.
                if self._has_border and self._can_scroll:
                    if self._scroll_bar.process_event(event):
                        return None

        # Don't allow events to bubble down if this window owns the Screen (as already
        # calculated when taking te focus) or if the Frame is modal or we handled the
        # event.
        return None if claimed_focus or self._is_modal or event is None else old_event

    def _switch_to_nearest_vertical_widget(self, direction):
        """
        Find the nearest widget above or below the current widget with the focus.

        This should only be called by the Frame when normal Layout navigation fails and so this needs to find
        the nearest widget in the next available Layout.  It will not search the existing Layout for a closer
        match.

        :param direction: The direction to move through the Layouts.
        """
        current_widget = self._layouts[self._focus].get_current_widget()
        focus = self._focus
        focus += direction
        while self._focus != focus:
            if focus < 0:
                focus = len(self._layouts) - 1
            if focus >= len(self._layouts):
                focus = 0
            match = self._layouts[focus].get_nearest_widget(current_widget, direction)
            if match:
                self.switch_focus(self._layouts[focus], match[1], match[2])
                return
            focus += direction

    def _find_next_tab_stop(self, direction):
        old_focus = self._focus
        self._focus += direction
        while self._focus != old_focus:
            if self._focus < 0:
                self._focus = len(self._layouts) - 1
            if self._focus >= len(self._layouts):
                self._focus = 0
            try:
                if direction > 0:
                    self._layouts[self._focus].focus(force_first=True)
                else:
                    self._layouts[self._focus].focus(force_last=True)
                break
            except IndexError:
                self._focus += direction

def custom_auth(library, *args):
    """Imports and runs 'library'"""
    split_lib = library.split(".")
    imported = __import__(split_lib[0], fromlist=[split_lib[1]])
    return getattr(imported, split_lib[1])(*args)
