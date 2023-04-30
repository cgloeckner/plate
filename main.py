import pygame
import moderngl
import math
import random

from core import app, resources, particles, render


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.cache = resources.Cache(engine.context)

        self.tex0 = self.cache.get_png('data/sprites/ship.png')
        self.tex0.filter = moderngl.NEAREST, moderngl.NEAREST
        self.tex1 = self.cache.get_svg('data/sprites/ufo.svg', scale=5)
        self.tex1.filter = moderngl.NEAREST, moderngl.NEAREST

        self.camera = render.Camera(engine.context, self.cache)

        self.s1 = render.Sprite(self.tex0, clip=pygame.Rect(0, 0, 32, 32))

        self.forward = pygame.math.Vector2(0, 1)
        self.right = pygame.math.Vector2(1, 0)

        self.s2 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s2.center.y = 250

        self.s3 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s3.center.x = 150

        self.total_ms = 0

        w, h = pygame.display.get_window_size()
        stars_surface = pygame.Surface((w, h))
        for _ in range(int((w * h) ** 0.5)):
            x = random.randrange(w)
            y = random.randrange(h)
            v = random.randrange(255)
            color = pygame.Color(v, v, v, 255)
            pygame.draw.rect(stars_surface, color, (x, y, 1.0, 1.0))

        stars_img_data = pygame.image.tostring(stars_surface, 'RGBA', True)
        self.stars_texture = self.engine.context.texture(size=stars_surface.get_size(), components=4,
                                                         data=stars_img_data)

        self.tile = render.Sprite(self.stars_texture)
        self.tile.clip.w *= 10
        self.tile.clip.h *= 10

        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 5000, 128)

    def emit_particles(self) -> None:
        size = self.camera.get_rect().size
        pos = pygame.math.Vector2(pygame.mouse.get_pos()) / self.camera.zoom
        pos.y = size[1] - pos.y
        pos += self.camera.get_rect().topleft

        impact = self.s1.center - pos
        impact.normalize_ip()

        color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))

        self.parts.emit(100, impact, 45, pos, 5.0, 20.0, color)

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

        if event.type == pygame.MOUSEBUTTONUP:
            self.s1.brightness = 5.0
            self.emit_particles()

    def update(self, elapsed_ms) -> None:
        self.s1.scale.x = 1 + math.sin(self.total_ms / 250) * 0.05
        self.s1.scale.y = 1 + math.sin(self.total_ms / 250) * 0.05

        if self.s1.brightness > 1.0:
            self.s1.brightness -= 0.01 * elapsed_ms
            if self.s1.brightness < 1.0:
                self.s1.brightness = 1.0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.s1.center += self.right.rotate(self.s1.rotation) * -0.5 * elapsed_ms
        if keys[pygame.K_d]:
            self.s1.center += self.right.rotate(self.s1.rotation) * 0.5 * elapsed_ms
        if keys[pygame.K_s]:
            self.s1.center += self.forward.rotate(self.s1.rotation) * -0.5 * elapsed_ms
        if keys[pygame.K_w]:
            self.s1.center += self.forward.rotate(self.s1.rotation) * 0.5 * elapsed_ms
        if keys[pygame.K_q]:
            self.s1.rotation += 0.1 * elapsed_ms
        if keys[pygame.K_e]:
            self.s1.rotation -= 0.1 * elapsed_ms
        if keys[pygame.K_PLUS]:
            self.camera.zoom *= (1 + 0.001 * elapsed_ms)
            if self.camera.zoom > 5.0:
                self.camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            self.camera.zoom *= (1 - 0.001 * elapsed_ms)
            if self.camera.zoom < 0.1:
                self.camera.zoom = 0.1

        self.camera.center = self.s1.center.copy()
        self.camera.update()

        self.parts.update(elapsed_ms)
        num_parts = self.parts.get_particle_count()

        self.total_ms += elapsed_ms
        pygame.display.set_caption(f'{int(self.engine.clock.get_fps())} FPS | {num_parts} Particles')

    def render(self) -> None:
        self.camera.render(self.tile)
        self.camera.render_particles(self.parts)
        self.camera.render(self.s2)
        self.camera.render(self.s3)
        self.camera.render(self.s1)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
