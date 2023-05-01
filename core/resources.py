"""Provides a resource cache for loading various resources from disk.
"""

import pygame
import moderngl
import io
import cairosvg

from typing import Dict, Tuple


class Cache:
    """Manages loading and caching data from disk."""

    def __init__(self, context: moderngl.Context) -> None:
        """Initializes the resource caches."""
        self.context = context
        self.png_cache: Dict[str, moderngl.Texture] = dict()
        self.svg_cache: Dict[Tuple[str, float], moderngl.Texture] = dict()
        self.shader_cache: Dict[str, str] = dict()

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
        """Loads an SVG file from path, scaling it as provided and returns the corresponding texture."""
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

    def get_shader(self, path: str) -> str:
        """Loads a shader sourcefile from path."""
        if path not in self.shader_cache:
            # load source from file
            with open(path, 'r') as handle:
                self.shader_cache[path] = handle.read()

        return self.shader_cache[path]

    def get_font(self, font_name: str = '', font_size: int = 18) -> pygame.font.Font:
        """Loads a SysFont via filename and font size."""
        if font_name == '':
            return pygame.font.SysFont(pygame.font.get_default_font(), font_size)

        raise NotImplementedError()
