import pygame
import moderngl

from typing import Optional

from . import sprite, resources


class Text:
    def __init__(self, context: moderngl.Context, font: pygame.font.Font):
        self._context = context
        self._font = font
        self.sprite: Optional[sprite.Sprite] = None

    def set_string(self, text: str, antialias: bool = True, color: pygame.Color = pygame.Color('white')) -> None:
        surface = self._font.render(text, antialias, color)
        texture = resources.texture_from_surface(self._context, surface)

        if self.sprite is not None:
            self.sprite.texture.release()

        self.sprite = sprite.Sprite(texture)
        self.sprite.origin.x = 0
        self.sprite.origin.y = 0
