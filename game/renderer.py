import moderngl
import pygame
import random

import core
from game import scene


class RendererSystem(scene.BaseSystem):
    def __init__(self, scene_obj: scene.Scene):
        super().__init__(scene_obj)

        # setup asteroids rendering batch
        asteroids_tex = scene_obj.engine.cache.get_svg('data/sprites/asteroid.svg', scale=10)
        asteroids_tex.filter = moderngl.NEAREST, moderngl.NEAREST
        self.asteroids = core.RenderBatch(scene_obj.engine.context, scene_obj.engine.cache, 10_000, scene_obj.asteroids,
                                          asteroids_tex)

        # setup spacecraft rendering batch
        spacecraft_tex = scene_obj.engine.cache.get_png('data/sprites/ship.png')
        spacecraft_tex.filter = moderngl.NEAREST, moderngl.NEAREST
        self.spacecrafts = core.RenderBatch(scene_obj.engine.context, scene_obj.engine.cache, 2_000,
                                            scene_obj.spacecrafts, spacecraft_tex)

        # setup starfield sprite
        w, h = pygame.display.get_window_size()
        num_stars = int(min(w, h) ** 0.5)
        surface = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        for _ in range(num_stars):
            x = random.randrange(w)
            y = random.randrange(h)
            v = random.randrange(255)
            color = pygame.Color(v, v, v, 255)
            pygame.draw.circle(surface, color, (x, y), 2.0)

        texture = scene_obj.engine.cache.texture_from_surface(scene_obj.engine.context, surface)
        texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.starfield_sprite = core.Sprite(texture=texture, origin=pygame.Vector2())
        self.starfield_sprite.clip.w *= 10
        self.starfield_sprite.clip.h *= 10

    def update(self, elapsed_ms: int) -> None:
        pass

    def render(self) -> None:
        self.scene.camera.render(self.starfield_sprite)  # FIXME: is not rendered atm.. idk why
        self.scene.camera.render_batch(self.asteroids)
        self.scene.camera.render_particles(self.scene.particles)
        self.scene.camera.render_batch(self.spacecrafts)
