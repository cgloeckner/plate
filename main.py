import pygame
import moderngl
import random

from core import app, resources, particles, render
import asteroids


class StarField:
    def __init__(self, context: moderngl.Context, width: int, height: int, num_stars: int):
        surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        for _ in range(num_stars):
            x = random.randrange(width)
            y = random.randrange(height)
            v = random.randrange(255)
            color = pygame.Color(v, v, v, 255)
            pygame.draw.circle(surface, color, (x, y), 2.0)

        self.texture = resources.texture_from_surface(context, surface)
        self.texture.filter = moderngl.NEAREST, moderngl.NEAREST

        self.sprite = render.Sprite(self.texture)
        self.sprite.origin.x = 0
        self.sprite.origin.y = 0


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.cache = resources.Cache(engine.context)

        self.tex0 = self.cache.get_png('data/sprites/ship.png')
        self.tex0.filter = moderngl.NEAREST, moderngl.NEAREST
        self.tex1 = self.cache.get_svg('data/sprites/ufo.svg', scale=5)
        self.tex1.filter = moderngl.NEAREST, moderngl.NEAREST

        self.camera = render.Camera(engine.context, self.cache)
        self.gui = render.GuiCamera(engine.context, self.cache)

        self.s1 = render.Sprite(self.tex0, clip=pygame.Rect(0, 0, 32, 32))

        self.forward = pygame.math.Vector2(0, 1)
        self.right = pygame.math.Vector2(1, 0)

        self.s2 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s2.center.y = 250

        self.s3 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s3.center.x = 150

        self.v1 = pygame.math.Vector2(0, 0)

        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 5000, 128)

        w, h = pygame.display.get_window_size()
        self.starfield = StarField(self.engine.context, w, h, int(min(w, h) ** 0.5))
        self.starfield.sprite.clip.w *= 10
        self.starfield.sprite.clip.h *= 10

        self.asteroids = asteroids.AsteroidsField(self.engine.context, self.cache, 1000)
        for _ in range(1000):
            x = random.randrange(0, 1600 * 10)
            y = random.randrange(0, 900 * 10)
            scale = random.uniform(0.5, 4.0)
            direction = pygame.math.Vector2(0, 1).rotate(random.uniform(0.0, 360.0)) * random.uniform(0.5, 4.0)
            self.asteroids.add_asteroid(pygame.math.Vector2(x, y), scale, direction)

        self.total_ms = 0

        self.fps = render.Text(self.engine.context, self.cache.get_font(font_size=30))

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

        self.asteroids.update(elapsed_ms)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.v1 = self.forward.rotate(self.camera.rotation) * 0.5 * elapsed_ms

            impact = self.forward.rotate(self.s1.rotation)
            pos = self.s1.center.copy() - impact * 16
            self.parts.emit(1, impact=impact, delta_degree=170, origin=pos, radius=5.0, speed=20.0,
                            color=pygame.Color('orange'))

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
            self.fps.set_string(f'FPS: {num_fps}\n{len(self.parts)} Particles')
            self.total_ms -= 250

    def render(self) -> None:
        self.camera.render(self.starfield.sprite)
        self.camera.render_particles(self.parts)
        self.camera.render_batch(self.asteroids)
        self.camera.render(self.s2)
        self.camera.render(self.s3)
        self.camera.render(self.s1)

        self.gui.render_text(self.fps)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
