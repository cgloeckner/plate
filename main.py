import pygame
import moderngl
import random

from typing import Optional

from core import app, resources, particles, render


class Text:
    def __init__(self, context: moderngl.Context):
        self.context = context
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 36)
        self.sprite: Optional[render.Sprite] = None

    def update(self, num_fps: int) -> None:
        if self.sprite is not None:
            self.sprite.texture.release()

        surface = self.font.render(f'{num_fps}', False, 'white')
        img_data = pygame.image.tostring(surface, 'RGBA', True)
        texture = self.context.texture(size=surface.get_size(), components=4, data=img_data)
        texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.sprite = render.Sprite(texture)
        self.sprite.center.x = texture.size[0] // 2
        self.sprite.center.y = texture.size[1] // 2


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.cache = resources.Cache(engine.context)

        self.tex0 = self.cache.get_png('data/sprites/ship.png')
        self.tex0.filter = moderngl.NEAREST, moderngl.NEAREST
        self.tex1 = self.cache.get_svg('data/sprites/ufo.svg', scale=5)
        self.tex1.filter = moderngl.NEAREST, moderngl.NEAREST
        self.tex2 = self.cache.get_png('data/sprites/asteroid.png')
        self.tex2.filter = moderngl.NEAREST, moderngl.NEAREST

        self.camera = render.Camera(engine.context, self.cache)
        self.gui = render.GuiCamera(engine.context, self.cache)

        self.s1 = render.Sprite(self.tex0, clip=pygame.Rect(0, 0, 32, 32))

        self.forward = pygame.math.Vector2(0, 1)
        self.right = pygame.math.Vector2(1, 0)

        self.s2 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s2.center.y = 250

        self.s3 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s3.center.x = 150

        self.asteroids_batch = render.Batch(self.engine.context, self.cache, 1000)
        for _ in range(1000):
            s = render.Sprite(self.tex2)
            s.center.x = random.randrange(0, 1600 * 10)
            s.center.y = random.randrange(0, 900 * 10)
            s.rotation = random.uniform(0.0, 360.0)
            s.scale *= random.uniform(0.5, 4.0)
            self.asteroids_batch.append(s)

        self.v1 = pygame.math.Vector2(0, 0)

        w, h = pygame.display.get_window_size()
        stars_surface = pygame.Surface((w, h))
        for _ in range(int(min(w, h) ** 0.5)):
            x = random.randrange(w)
            y = random.randrange(h)
            v = random.randrange(255)
            color = pygame.Color(v, v, v, 255)
            pygame.draw.circle(stars_surface, color, (x, y), 2.0)

        stars_img_data = pygame.image.tostring(stars_surface, 'RGBA', True)
        self.stars_texture = self.engine.context.texture(size=stars_surface.get_size(), components=4,
                                                         data=stars_img_data)
        self.stars_texture.filter = moderngl.NEAREST, moderngl.NEAREST

        self.tile = render.Sprite(self.stars_texture)
        self.tile.clip.w *= 10
        self.tile.clip.h *= 10

        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 5000, 128)

        self.total_ms = 0

        self.fps = Text(self.engine.context)

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

        if event.type == pygame.MOUSEBUTTONUP:
            self.s1.brightness = 5.0

    def update(self, elapsed_ms) -> None:
        if self.s1.brightness > 1.0:
            self.s1.brightness -= 0.01 * elapsed_ms
            if self.s1.brightness < 1.0:
                self.s1.brightness = 1.0

        for index in range(self.asteroids_batch.renderer.max_num_sprites):
            self.asteroids_batch.renderer.data[index * 14] += elapsed_ms * 0.01
            self.asteroids_batch.renderer.data[index * 14 + 1] += elapsed_ms * 0.01
            self.asteroids_batch.renderer.data[index * 14 + 4] += elapsed_ms * 0.01

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.v1 = self.forward.rotate(self.camera.rotation) * 0.5 * elapsed_ms

            impact = self.forward.rotate(self.s1.rotation)
            pos = self.s1.center.copy() - impact * 32
            self.parts.emit(1, impact, 170, pos, 5.0, 20.0, pygame.Color('orange'))

        if keys[pygame.K_s]:
            # slow down
            self.v1 *= (1 - 0.001 * elapsed_ms)

        if keys[pygame.K_q]:
            self.camera.rotation += 0.05 * elapsed_ms
        if keys[pygame.K_e]:
            self.camera.rotation -= 0.05 * elapsed_ms

        if keys[pygame.K_PLUS]:
            self.camera.zoom *= (1 + 0.001 * elapsed_ms)
            if self.camera.zoom > 5.0:
                self.camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            self.camera.zoom *= (1 - 0.001 * elapsed_ms)
            if self.camera.zoom < 0.1:
                self.camera.zoom = 0.1

        self.v1 *= (1 - 0.001 * elapsed_ms)

        self.s1.rotation = self.camera.rotation
        self.s1.center += self.v1

        self.camera.center = self.s1.center.copy()
        self.camera.update()

        self.parts.update(elapsed_ms)

        self.total_ms += elapsed_ms
        num_fps = int(self.engine.clock.get_fps())
        if self.total_ms > 250:
            pygame.display.set_caption(f'{int(self.engine.clock.get_fps())} FPS')
            self.fps.update(num_fps)
            self.total_ms -= 250

    def render(self) -> None:
        self.camera.render(self.tile)
        self.camera.render_particles(self.parts)
        self.camera.render_batch(self.asteroids_batch)
        self.camera.render(self.s2)
        self.camera.render(self.s3)
        self.camera.render(self.s1)

        if self.fps.sprite is not None:
            self.gui.render(self.fps.sprite)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
