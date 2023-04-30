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
        self.tex2 = self.cache.get_png('data/sprites/asteroid.png')
        self.tex2.filter = moderngl.NEAREST, moderngl.NEAREST

        self.camera = render.Camera(engine.context, self.cache)

        self.s1 = render.Sprite(self.tex0, clip=pygame.Rect(0, 0, 32, 32))

        self.forward = pygame.math.Vector2(0, 1)
        self.right = pygame.math.Vector2(1, 0)

        self.s2 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s2.center.y = 250

        self.s3 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, self.tex1.size[1], self.tex1.size[1]))
        self.s3.center.x = 150

        self.asteroids = [render.Sprite(self.tex2) for _ in range(20)]
        for ast in self.asteroids:
            ast.center.x = random.randrange(0, 1600)
            ast.center.y = random.randrange(0, 900)
            ast.direction = pygame.math.Vector2()
            ast.direction.x = random.uniform(-1.0, 1.0)
            ast.direction.y = random.uniform(-1.0, 1.0)
            ast.angle = random.uniform(0.0, 5.0)

        self.v1 = pygame.math.Vector2(0, 0)

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
        self.stars_texture.filter = moderngl.NEAREST, moderngl.NEAREST

        self.tile = render.Sprite(self.stars_texture)
        self.tile.clip.w *= 10
        self.tile.clip.h *= 10

        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 5000, 128)

    def emit_particles(self) -> None:
        size = self.camera.get_rect().size
        pos = pygame.math.Vector2(pygame.mouse.get_pos())
        pos /= self.camera.zoom
        pos.y = size[1] - pos.y
        pos += self.camera.get_rect().topleft
        pos.rotate_ip(self.camera.rotation)
        pos = self.s1.center.copy()

        #impact = self.s1.center - pos
        #impact.normalize_ip()
        impact = self.forward.rotate(self.s1.rotation)

        color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))

        self.parts.emit(100, impact, 135, pos, 5.0, 20.0, color)

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

        if event.type == pygame.MOUSEBUTTONUP:
            self.s1.brightness = 5.0
            self.emit_particles()

    def update(self, elapsed_ms) -> None:
        if self.s1.brightness > 1.0:
            self.s1.brightness -= 0.01 * elapsed_ms
            if self.s1.brightness < 1.0:
                self.s1.brightness = 1.0

        for ast in self.asteroids:
            ast.center += ast.direction * 0.05 * elapsed_ms
            ast.rotation += ast.angle * 0.05 * elapsed_ms

        keys = pygame.key.get_pressed()
        binding = {
            #pygame.K_a: -self.right, pygame.K_d: self.right,
            pygame.K_w: self.forward, pygame.K_s: -self.forward
        }

        for key in binding:
            if keys[key]:
                self.v1 += binding[key].rotate(self.camera.rotation) * 0.0005 * elapsed_ms

        if keys[pygame.K_w]:
            impact = self.forward.rotate(self.s1.rotation)
            pos = self.s1.center.copy() - impact * 32
            self.parts.emit(1, impact, 170, pos, 5.0, 20.0, pygame.Color('orange'))

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

        if self.v1.length() > 1:
            self.v1 = self.v1.normalize() * 1
        self.v1 *= (1 - 0.0001 * elapsed_ms)

        self.s1.rotation = self.camera.rotation
        self.s1.center += self.v1

        self.camera.center = self.s1.center.copy()
        self.camera.update()

        self.parts.update(elapsed_ms)
        num_parts = self.parts.get_particle_count()

        self.total_ms += elapsed_ms
        pygame.display.set_caption(f'{int(self.engine.clock.get_fps())} FPS | {num_parts} Particles')

    def render(self) -> None:
        self.camera.render(self.tile)
        self.camera.render_particles(self.parts)
        for ast in self.asteroids:
            self.camera.render(ast)
        self.camera.render(self.s2)
        self.camera.render(self.s3)
        self.camera.render(self.s1)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
