#!/usr/bin/env python3
"""Postman like TUI"""
import sys
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from view.rest import RestView

def respyte_tui(screen, scene):
    """start playing tui scenes"""
    scenes = [
        Scene([RestView(screen)], -1, name="Main"),
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scene, allow_int=True)

def main():
    """injection point from terminal"""
    last_scene = None
    while True:
        try:
            Screen.wrapper(respyte_tui, catch_interrupt=True, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as err:
            last_scene = err.scene

if __name__ == "__main__":
    main()
