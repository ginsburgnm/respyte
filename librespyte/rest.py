#!/usr/bin/env python3
"""Main view of respyte"""
from os import path, remove
import json
import re
import yaml
import requests
import urllib3
from asciimatics.widgets import Button, Divider, DropdownList, Frame, Layout, Text, \
    TextBox, VerticalDivider, PopUpDialog
from asciimatics.exceptions import  StopApplication, NextScene
urllib3.disable_warnings()

CONFIG_DIRECTORY = path.expanduser(path.join("~", ".config", "respyte"))
HISTORY_FILE = path.join(CONFIG_DIRECTORY, "history.json")
SCRATCH_FILE = path.join(CONFIG_DIRECTORY, "scratch.json")

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

        theme = parsed_args.color_scheme
        self.set_theme(theme)
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
                                    disabled=True
                                    )
        req_layout.add_widget(self.resp_headers, 2)
        req_layout.add_widget(Divider(), 2)
        self.response = TextBox(screen.height // 4 * 3 - 7,
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
        button_layout.add_widget(Button("Send it", self._send), 0)
        button_layout.add_widget(Button("History", self._history), 1)
        button_layout.add_widget(Button("Quit", self._quit), 2)
        self._populate()
        self.fix()

    def _history(self):
        """Show history"""
        raise NextScene("History")

    def _populate(self):
        """populate information"""
        self.save()
        if path.isfile(SCRATCH_FILE) and path.isfile(HISTORY_FILE):
            with open(SCRATCH_FILE, 'r') as scratch_file:
                selection = json.loads(scratch_file.read())["history"]
            remove(SCRATCH_FILE)
            with open(HISTORY_FILE, 'r') as history_file:
                json_obj = json.loads(history_file.readlines()[selection])
                self.request.value = json.dumps(json_obj['data'])
                self.req_headers.value = json.dumps(json_obj['headers'])
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
            data = json.loads(self.data['req_params']) if self.data['req_params'] else {}
            self.request.value = json.dumps(data, indent=2, sort_keys=True)
            headers = json.loads(self.data['req_headers']) if self.data['req_headers'] else {}
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
                with open(HISTORY_FILE, "a+") as history_file:
                    history_file.write('\n')
                    history_file.write(json.dumps(history))

            except json.JSONDecodeError:
                self.response.value = req.text
            self.screen.refresh()
        except Exception as err: # pylint: disable=broad-except
            self.scene.add_effect(PopUpDialog(self.screen, str(err), ["Ok"]))

def custom_auth(library, *args):
    """Imports and runs 'library'"""
    split_lib = library.split(".")
    imported = __import__(split_lib[0], fromlist=[split_lib[1]])
    return getattr(imported, split_lib[1])(*args)
