"""Basic state machine for pygame/moderngl applications.

FIXME: I did not managed to get imgui work with OpenGL #330, hence imgui is disabled right now

based on https://github.com/pyimgui/pyimgui/blob/master/doc/examples/integrations_pygame.py
"""

import pygame
import moderngl
# FIXME
# import imgui
# from imgui.integrations.pygame import PygameRenderer

from typing import Optional, Dict
from abc import ABC, abstractmethod


class PerformanceMonitor:
    def __init__(self):
        self.elapsed_ms: Dict[str, int] = {}
        self._category: str = ''
        self._enter_ticks = 0

    def __enter__(self) -> None:
        self._enter_ticks = pygame.time.get_ticks()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        delta_time = pygame.time.get_ticks() - self._enter_ticks
        self.elapsed_ms[self._category] = delta_time

    def __call__(self, category: str) -> None:
        self._category = category

    def __str__(self) -> str:
        out = ''
        for key in self.elapsed_ms:
            out += f'{key}: {self.elapsed_ms[key]}ms\n'
        return out


# ----------------------------------------------------------------------------------------------------------------------


class Engine:
    """Manages the mainloop and holds a stack of game states, where the top one is handled until it quits."""

    def __init__(self, width: float, height: float, ini_file: Optional[str] = None,
                 log_file: Optional[str] = None) -> None:
        """Create window and opengl context from the given resolution.

        FIXME: document ini_file and log_file as soon as imgui works
        """
        # setup pygame to work with opengl
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # create opengl context
        pygame.display.set_mode((width, height), flags=pygame.OPENGL | pygame.DOUBLEBUF)
        self.context = moderngl.create_context()
        self.context.enable(moderngl.BLEND)  # required for alpha stuff

        # prepare imgui
        # FIXME
        # imgui.create_context()
        # self._impl = PygameRenderer()
        # self.imgui_io = imgui.get_io()
        # self.imgui_io.display_size = (width, height)
        # self.imgui_io.ini_file_name = ini_file
        # self.imgui_io.log_file_name = log_file

        # prepare mainloop
        self.clock = pygame.time.Clock()
        self.max_fps = 800
        self._queue = list()

        self.perf_monitor = PerformanceMonitor()

    def __del__(self):
        """Quit pygame when the engine is destroyed."""
        pygame.quit()

    def push(self, state: 'State') -> None:
        """Push the given state to the stack, so it will be processed as soon as possible."""
        self._queue.append(state)

    def pop(self) -> None:
        """Pops the current state from the stack."""
        self._queue.pop()

    def run(self) -> None:
        """Mainloop that forwards events, updates and renders the game state."""
        while True:
            # grab top state
            try:
                state = self._queue[-1]
            except IndexError:
                # quit mainloop
                break

            with self.perf_monitor:
                self.perf_monitor('input_events')

                # handle events
                for event in pygame.event.get():
                    # FIXME
                    # self._impl.process_event(event)
                    state.process_event(event)

            # update app logic
            elapsed_ms = self.clock.tick(self.max_fps)
            # FIXME
            # imgui.new_frame()

            state.update(elapsed_ms)

            # render app
            with self.perf_monitor:
                self.perf_monitor('opengl_render')

                self.context.clear()
                state.render()
                # FIXME
                # imgui.render()
                # self._impl.render(imgui.get_draw_data())
                pygame.display.flip()


class State(ABC):
    """Abstract state class. Derive to create a custom game state (e.g. pause screen)."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @abstractmethod
    def process_event(self, event: pygame.event.Event) -> None: ...

    @abstractmethod
    def update(self, elapsed_ms: int) -> None: ...

    @abstractmethod
    def render(self) -> None: ...
