import random
import math

import moderngl
import pygame
import pygame.gfxdraw

import core
from game import scene


STARFIELD_LOD: int = 4


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
        self.starfield_tex = self.generate_starfield(*pygame.display.get_window_size(), 200)
        self.starfield_array = core.SpriteArray()
        self.starfield = core.RenderBatch(scene_obj.engine.context, scene_obj.engine.cache, 1_000,
                                          self.starfield_array, self.starfield_tex)

        self.lightmap = core.create_lightmap(scene_obj.engine.context, 1_000)
        self.light_sprite = core.Sprite(self.lightmap)
        self.light_sprite.color = pygame.Color('yellow')
        self.light_sprite.color.a = 50

    def generate_starfield(self, width: int, height: int, num_stars: int) -> moderngl.Texture:
        width *= STARFIELD_LOD
        height *= STARFIELD_LOD
        surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        for _ in range(num_stars):
            x = random.randrange(width - 8 * STARFIELD_LOD) + 4 * STARFIELD_LOD
            y = random.randrange(height - 8 * STARFIELD_LOD) + 4 * STARFIELD_LOD
            v = random.randrange(255)
            color = pygame.Color(v, v, v, 255)
            for radius in reversed(range(STARFIELD_LOD)):
                color_step = (color.r, color.g, color.b, 255 - int(color.a * radius / STARFIELD_LOD))
                pygame.draw.circle(surface, color_step, (x, y), radius * random.uniform(2.0, 4.0))

        texture = core.texture_from_surface(self.scene.engine.context, surface)
        texture.filter = moderngl.NEAREST, moderngl.NEAREST

        return texture

    def continue_starfield(self, x: float, y: float) -> None:
        size = pygame.display.get_window_size()
        cell_x = int(x) // size[0]
        cell_y = int(y) // size[1]

        cam_size = self.scene.camera.get_size()
        x_border = int(math.ceil(cam_size[0] / size[0])) + 1
        y_border = int(math.ceil(cam_size[1] / size[1])) + 1

        self.starfield_array.clear()
        for dy in range(-y_border, y_border+1):
            for dx in range(-x_border, x_border+1):
                s = core.Sprite(texture=self.starfield_tex, origin=pygame.Vector2())
                s.center.x = (cell_x + dx) * size[0] - size[0] // 2
                s.center.y = (cell_y + dy) * size[1] - size[1] // 2
                s.scale /= 4
                self.starfield_array.add(s)

    def update(self, elapsed_ms: int) -> None:
        pass

    def render(self) -> None:
        self.scene.camera.render_batch(self.starfield)

        #self.light_sprite.center.x = self.scene.spacecrafts.data[0, core.SpriteOffset.POS_X]
        #self.light_sprite.center.y = self.scene.spacecrafts.data[0, core.SpriteOffset.POS_Y]
        #self.scene.camera.render(self.light_sprite)

        self.scene.camera.render_batch(self.asteroids)
        self.scene.camera.render_particles(self.scene.particles)
        self.scene.camera.render_batch(self.spacecrafts)

