import pygame

from abc import ABC, abstractmethod

import core


class Scene:
    def __init__(self, engine: core.Engine) -> None:
        self.engine = engine

        self.spacecrafts = core.SpriteArray()
        self.asteroids = core.SpriteArray()

        self.particles = core.ParticleSystem(engine.context, engine.cache, 5000, 128)
        self.camera = core.Camera(engine.context, engine.cache)
        self.gui = core.GuiCamera(engine.context, engine.cache)


class BaseSystem(ABC):
    def __init__(self, scene: Scene) -> None:
        self.scene = scene

    @abstractmethod
    def update(self, elapsed_ms: int) -> None: ...
