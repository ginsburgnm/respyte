#!/usr/bin/env python3
"""Postman like TUI"""
from os import path
import sys
import configargparse
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from librespyte.rest import RestView

def parse():
    """adds and parses arguments"""
    data = ".respyterc"
    default = path.join(path.expanduser("~"), data + ".yml")
    parser = configargparse.ArgParser(
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        default_config_files=[default])
    parser.add(
        '-c', '--color-scheme',
        default="bright",
        help='color scheme to use [monochrome, green, bright, tlj256, blue] defaults to bright'
    )
    return parser.parse_args()

def respyte_tui(screen, scene, parsed_args):
    """start playing tui scenes"""
    scenes = [
        Scene([RestView(screen, parsed_args)], -1, name="Main"),
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scene, allow_int=True)

def main():
    """injection point from terminal"""
    parsed_args = parse()
    last_scene = None
    while True:
        try:
            Screen.wrapper(respyte_tui, catch_interrupt=True, arguments=[last_scene, parsed_args])
            sys.exit(0)
        except ResizeScreenError as err:
            last_scene = err.scene

if __name__ == "__main__":
    sys.path.append('.')
    main()
