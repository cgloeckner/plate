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

        self.particles = core.ParticleSystem(engine.context, engine.cache, 50_000, 128)
        self.camera = core.Camera(engine.context, engine.cache)
        self.gui = core.GuiCamera(engine.context, engine.cache)

    def explode_spacecrafts(self, indices: List[int]) -> None:
        if len(indices) == 0:
            return

        print(indices)

        for index in indices:
            pos = pygame.math.Vector2(
                *self.spacecrafts.data[index, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y+1])
            for _ in range(150):
                self.particles.emit(origin=pos, radius=5.0, spread=10.0, speed=10.0, color=pygame.Color('white'))

        tmp = sorted(indices, reverse=True)
        self.spacecrafts.data = numpy.delete(self.spacecrafts.data, tmp, axis=0)


class BaseSystem(ABC):
    def __init__(self, scene: Scene) -> None:
        self.scene = scene

    @abstractmethod
    def update(self, elapsed_ms: int) -> None: ...
