"""Basic state machine for pygame/moderngl applications.

FIXME: I did not managed to get imgui work with OpenGL #330, hence imgui is disabled right now

based on https://github.com/pyimgui/pyimgui/blob/master/doc/examples/integrations_pygame.py
"""

import pygame
import moderngl
import io
import cairosvg
# FIXME
# import imgui
# from imgui.integrations.pygame import PygameRenderer

from typing import Dict, Tuple, Optional
from abc import abstractmethod, ABC


class ResourceCache:
    """Manages loading and caching data from disk."""

    def __init__(self, context: moderngl.Context) -> None:
        """Initializes the resource caches."""
        self.context = context
        self.png_cache: Dict[str, moderngl.Texture] = dict()
        self.svg_cache: Dict[Tuple[str, float], moderngl.Texture] = dict()

    def get_png(self, path: str) -> moderngl.Texture:
        """Loads a PNG file from path and returns the corresponding texture."""
        if path not in self.png_cache:
            # load image file
            surface = pygame.image.load(path)
            img_data = pygame.image.tostring(surface, 'RGBA', True)

            # load texture from surface
            texture = self.context.texture(size=surface.get_size(), components=4, data=img_data)
            self.png_cache[path] = texture

        return self.png_cache[path]

    def get_svg(self, path: str, scale: float) -> moderngl.Texture:
        """Loads a SVG file from path, scaling it as provided and returns the corresponding texture."""
        key = (path, scale)

        if key not in self.svg_cache:
            # rasterize vector graphics
            png_data = cairosvg.svg2png(url=path, scale=scale)
            surface = pygame.image.load(io.BytesIO(png_data))
            img_data = pygame.image.tostring(surface, 'RGBA', True)

            # load texture from surface
            texture = self.context.texture(size=surface.get_size(), components=4, data=img_data)
            self.svg_cache[key] = texture

        return self.svg_cache[key]


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
