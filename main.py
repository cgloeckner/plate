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


class Fighter:
    def __init__(self, cache: resources.Cache, particle_system: particles.ParticleSystem):
        self.particle_system = particle_system

        self.tex = cache.get_png('data/sprites/ship.png')
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST

        self.sprite = render.Sprite(self.tex, clip=pygame.Rect(0, 0, 32, 32))
        self.forward = pygame.math.Vector2(0, 1)
        self.velocity = pygame.math.Vector2()

    def flash(self) -> None:
        self.sprite.brightness = 5.0

    def accelerate(self, elapsed_ms: int) -> None:
        self.velocity = self.forward.rotate(self.sprite.rotation) * 0.5 * elapsed_ms

        impact = self.forward.rotate(self.sprite.rotation)
        pos = self.sprite.center.copy() - impact * 16
        self.particle_system.emit(1, impact=impact, delta_degree=170, origin=pos, radius=5.0, speed=20.0,
                                  color=pygame.Color('orange'))

    def decelerate(self, elapsed_ms: int) -> None:
        self.velocity *= (1 - 0.001 * elapsed_ms)

    def rotate(self, elapsed_ms: int) -> None:
        # NOTE: elapsed_ms is negative if rotating in the opposite direction
        self.sprite.rotation += 0.05 * elapsed_ms

    def update(self, elapsed_ms: int) -> None:
        if self.sprite.brightness > 1.0:
            self.sprite.brightness -= 0.01 * elapsed_ms
            if self.sprite.brightness < 1.0:
                self.sprite.brightness = 1.0

        # apply velocity and let it slowly decay
        self.sprite.center += self.velocity
        self.velocity *= (1 - 0.001 * elapsed_ms)


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.cache = resources.Cache(engine.context)
        self.camera = render.Camera(engine.context, self.cache)
        self.gui = render.GuiCamera(engine.context, self.cache)
        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 5000, 128)

        # create starfield background
        w, h = pygame.display.get_window_size()
        self.starfield = StarField(self.engine.context, w, h, int(min(w, h) ** 0.5))
        self.starfield.sprite.clip.w *= 10
        self.starfield.sprite.clip.h *= 10

        # create asteroids field
        self.asteroids = asteroids.AsteroidsField(self.engine.context, self.cache, 1000)
        for _ in range(1000):
            x = random.randrange(0, 1600 * 10)
            y = random.randrange(0, 900 * 10)
            scale = random.uniform(0.5, 4.0)
            direction = pygame.math.Vector2(0, 1).rotate(random.uniform(0.0, 360.0)) * random.uniform(0.5, 4.0)
            self.asteroids.add_asteroid(pygame.math.Vector2(x, y), scale, direction)

        self.total_ms = 0
        self.fps = render.Text(self.engine.context, self.cache.get_font(font_size=30))

        # create fighters
        self.fighters = [Fighter(self.cache, self.parts) for _ in range(2)]
        self.fighters[1].sprite.center.x -= 200
        self.fighters[1].sprite.center.y -= 200
        self.fighters[1].sprite.color = pygame.Color('red')
        self.fighters[1].sprite.color.a = 96
        #self.fighters[2].sprite.center.x += 200
        #self.fighters[2].sprite.center.y -= 200
        #self.fighters[2].sprite.color = pygame.Color('blue')
        #self.fighters[2].sprite.color.a = 96

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

    def update_enemy(self, fighter: Fighter, elapsed_ms: int) -> None:
        direction = self.fighters[0].sprite.center - fighter.sprite.center
        delta = fighter.forward.rotate(fighter.sprite.rotation).angle_to(direction)
        if delta < 0:
            fighter.rotate(-elapsed_ms * 10)
        if delta > 0:
            fighter.rotate(elapsed_ms * 10)

        if self.total_ms < 100:
            fighter.accelerate(elapsed_ms)

    def update_player(self, fighter: Fighter, elapsed_ms: int) -> None:
        keys = pygame.key.get_pressed()

        # basic controls
        if keys[pygame.K_w]:
            fighter.accelerate(elapsed_ms)
        if keys[pygame.K_s]:
            fighter.decelerate(elapsed_ms)
        if keys[pygame.K_q]:
            fighter.rotate(elapsed_ms)
        if keys[pygame.K_e]:
            fighter.rotate(-elapsed_ms)

        # zoom
        if keys[pygame.K_PLUS]:
            self.camera.zoom *= (1 + 0.001 * elapsed_ms)
            if self.camera.zoom > 5.0:
                self.camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            self.camera.zoom *= (1 - 0.001 * elapsed_ms)
            if self.camera.zoom < 0.1:
                self.camera.zoom = 0.1

        # let camera follow player
        self.camera.center = fighter.sprite.center.copy()
        self.camera.rotation = fighter.sprite.rotation

    def update(self, elapsed_ms) -> None:
        self.total_ms += elapsed_ms

        self.asteroids.update(elapsed_ms)
        self.update_player(self.fighters[0], elapsed_ms)
        for index, f in enumerate(self.fighters):
            if index > 0:
                self.update_enemy(f, elapsed_ms)
            f.update(elapsed_ms)

        self.camera.update()
        self.parts.update(elapsed_ms)

        num_fps = int(self.engine.clock.get_fps())
        if self.total_ms > 250:
            self.fps.set_string(f'FPS: {num_fps}\n{len(self.parts)} Particles')
            self.total_ms -= 250

    def render(self) -> None:
        self.camera.render(self.starfield.sprite)
        self.camera.render_particles(self.parts)
        self.camera.render_batch(self.asteroids)
        for f in self.fighters:
            self.camera.render(f.sprite)

        self.gui.render_text(self.fps)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
