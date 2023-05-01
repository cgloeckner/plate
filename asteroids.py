import moderngl
import pygame
import array
import random

from core import resources, render


class AsteroidsField(render.RenderBatch):
    def __init__(self, context: moderngl.Context, cache: resources.Cache, field_size: int):
        super().__init__(context, cache, field_size)

        self.tex = cache.get_svg('data/sprites/asteroid.svg', scale=10)
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST

        self.velocity = array.array('f')

    def add_asteroid(self, center: pygame.math.Vector2, scale: float, velocity: pygame.math.Vector2) -> None:
        s = render.Sprite(self.tex)
        s.center = center
        s.rotation = random.uniform(0.0, 360.0)
        s.scale *= scale / 10
        self.append(s)
        self.velocity.extend(velocity.xy)

    def update(self, elapsed_ms: int) -> None:
        delta = elapsed_ms * 0.01
        for index in range(len(self)):
            self.data[index * len(render.Offset) + render.Offset.POS_X] += self.velocity[index * 2] * delta
            self.data[index * len(render.Offset) + render.Offset.POS_Y] += self.velocity[index * 2 + 1] * delta
            self.data[index * len(render.Offset) + render.Offset.ROTATION] += delta
