import numpy
import pygame

from typing import List
from abc import ABC, abstractmethod

import core


class Scene:
    def __init__(self, engine: core.Engine) -> None:
        self.engine = engine

        self.spacecrafts = core.SpriteArray()
        self.asteroids = core.SpriteArray()

        shaders = engine.cache.get_shaders('data/glsl/particles', ['vert', 'geom', 'frag'])
        self.particles = core.ParticleSystem(engine.context, 50_000, 128, *shaders)
        self.camera = core.Camera(engine.context, engine.cache)
        self.gui = core.GuiCamera(engine.context, engine.cache)

    def explode_spacecrafts(self, indices: List[int]) -> None:
        if len(indices) == 0:
            return

        print(indices)

        for index in indices:
            pos = core.Sprite.get_center(self.spacecrafts.data[index])
            for _ in range(150):
                self.particles.emit(origin=pos, radius=5.0, spread=10.0, speed=10.0, color=pygame.Color('white'))

        tmp = sorted(indices, reverse=True)
        self.spacecrafts.data = numpy.delete(self.spacecrafts.data, tmp, axis=0)


class BaseSystem(ABC):
    def __init__(self, scene: Scene) -> None:
        self.scene = scene

    @abstractmethod
    def update(self, elapsed_ms: int) -> None: ...
