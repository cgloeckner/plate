import pygame
import moderngl
import random
import numpy

from core import app, resources, particles, render, sprite, text


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

        self.sprite = sprite.Sprite(self.texture)
        self.sprite.origin.x = 0
        self.sprite.origin.y = 0


class AsteroidsField(render.RenderBatch):
    def __init__(self, context: moderngl.Context, cache: resources.Cache, field_size: int):
        self.sprites = sprite.SpriteArray()
        super().__init__(context, cache, field_size, self.sprites)

        self.tex = cache.get_svg('data/sprites/asteroid.svg', scale=10)
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST

    def add_asteroid(self, center: pygame.math.Vector2, scale: float, velocity: pygame.math.Vector2) -> None:
        s = sprite.Sprite(self.tex)
        s.center = center
        s.rotation = random.uniform(0.0, 360.0)
        s.scale *= scale / 10
        s.velocity = velocity
        self.add(s)

    def update(self, elapsed_ms: int) -> None:
        sprite.update_movement(self.sprites, elapsed_ms)

        # update rotation
        self.sprites.data[:, sprite.Offset.ROTATION] += elapsed_ms * 0.01


BREAK: float = 0.0015


class FighterSystem(render.RenderBatch):
    def __init__(self, context: moderngl.Context, cache: resources.Cache, particle_system: particles.ParticleSystem,
                 num_max_fighters: int):
        self.sprites = sprite.SpriteArray()
        super().__init__(context, cache, num_max_fighters, self.sprites)
        self.particle_system = particle_system

        self.tex = cache.get_png('data/sprites/ship.png')
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST

        self.forward = pygame.math.Vector2(0, 1)

    def accelerate(self, index: int, elapsed_ms: int) -> None:
        rot = self.sprites.data[index, sprite.Offset.ROTATION]

        vel = self.forward.rotate(rot)
        self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1] = vel.xy

        impact = self.forward.rotate(rot)
        pos = pygame.math.Vector2(*self.sprites.data[index, sprite.Offset.POS_X:sprite.Offset.POS_Y+1]) - impact * 16
        if random.random() > 0.75:
            self.particle_system.emit(origin=pos, radius=5.0, color=pygame.Color('orange'), impact=impact,
                                      delta_degree=170)

    def decelerate(self, index: int,elapsed_ms: int) -> None:
        self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1] *= numpy.exp(-BREAK * elapsed_ms)

    def rotate(self, index: int,elapsed_ms: int) -> None:
        # NOTE: elapsed_ms is negative if rotating in the opposite direction
        delta = 0.075 * elapsed_ms

        vel_x, vel_y = self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1]
        vel = pygame.math.Vector2(vel_x, vel_y).rotate(delta)
        self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1] = vel.xy

        self.sprites.data[index, sprite.Offset.ROTATION] += delta

    """
    def flash(self) -> None:
        self.sprite.brightness = 5.0

    def update(self, elapsed_ms: int) -> None:
        if self.sprite.brightness > 1.0:
            self.sprite.brightness -= 0.01 * elapsed_ms
            if self.sprite.brightness < 1.0:
                self.sprite.brightness = 1.0

        # apply velocity and let it slowly decay
        self.sprite.center += self.velocity
        self.velocity *= (1 - 0.001 * elapsed_ms)
    """

    def update(self, elapsed_ms: int) -> None:
        sprite.update_movement(self.sprites, elapsed_ms)

    def update_enemy(self, index: int, elapsed_ms: int, total_ms: int) -> None:
        player_pos = pygame.math.Vector2(*self.sprites.data[0, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
        own_pos = pygame.math.Vector2(*self.sprites.data[index, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
        direction = player_pos - own_pos

        if direction.length() > 10000.0:
            self.decelerate(index, elapsed_ms)
            return

        delta = self.forward.rotate(self.sprites.data[index, sprite.Offset.ROTATION]).angle_to(direction)

        if delta < 0:
            self.rotate(index, -elapsed_ms)
        if delta > 0:
            self.rotate(index, elapsed_ms)

        if total_ms < 100:
            self.accelerate(index, elapsed_ms)


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.cache = resources.Cache(engine.context)
        self.camera = render.Camera(engine.context, self.cache)
        self.gui = render.GuiCamera(engine.context, self.cache)
        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 50000, 128)

        # create starfield background
        w, h = pygame.display.get_window_size()
        self.starfield = StarField(self.engine.context, w, h, int(min(w, h) ** 0.5))
        self.starfield.sprite.clip.w *= 10
        self.starfield.sprite.clip.h *= 10

        # create asteroids field
        self.asteroids = AsteroidsField(self.engine.context, self.cache, 10000)
        for _ in range(1000):
            x = random.randrange(0, 1600 * 10)
            y = random.randrange(0, 900 * 10)
            scale = random.uniform(0.5, 4.0)
            direction = pygame.math.Vector2(0, 1).rotate(random.uniform(0.0, 360.0)) * random.uniform(0.5, 4.0)
            direction *= 0.01
            self.asteroids.add_asteroid(pygame.math.Vector2(x, y), scale, direction)

        self.total_ms = 0
        self.fps = text.Text(self.engine.context, self.cache.get_font(font_size=30))

        # create fighters
        self.fighters = FighterSystem(self.engine.context, self.cache, self.parts, 1000)
        s = sprite.Sprite(self.fighters.tex, clip=pygame.Rect(0, 0, 32, 32))
        self.fighters.add(s)

        for i in range(100):
            s = sprite.Sprite(self.fighters.tex, clip=pygame.Rect(0, 0, 32, 32))
            s.center.x -= 200 + i * 50
            s.center.y -= 200 + i * 50
            s.color = pygame.Color('red')
            s.color.a = 96
            self.fighters.add(s)

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

    def update_player(self, elapsed_ms: int) -> None:
        keys = pygame.key.get_pressed()

        # basic controls
        if keys[pygame.K_w]:
            self.fighters.accelerate(0, elapsed_ms)
        if keys[pygame.K_s]:
            self.fighters.decelerate(0, elapsed_ms)
        if keys[pygame.K_q]:
            self.fighters.rotate(0, elapsed_ms)
        if keys[pygame.K_e]:
            self.fighters.rotate(0, -elapsed_ms)

        # zoom
        if keys[pygame.K_PLUS]:
            self.camera.zoom *= (1 + 0.001 * elapsed_ms)
            if self.camera.zoom > 5.0:
                self.camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            self.camera.zoom *= (1 - 0.001 * elapsed_ms)
            if self.camera.zoom < 0.1:
                self.camera.zoom = 0.1

    def update(self, elapsed_ms) -> None:
        self.total_ms += elapsed_ms

        self.update_player(elapsed_ms)
        for index in range(len(self.fighters) - 1):
            self.fighters.update_enemy(index + 1, elapsed_ms, self.total_ms)

        self.asteroids.update(elapsed_ms)
        self.fighters.update(elapsed_ms)

        # let camera follow player
        self.camera.center = pygame.math.Vector2(
            *self.fighters.sprites.data[0, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
        self.camera.rotation = self.fighters.sprites.data[0, sprite.Offset.ROTATION]

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
        self.camera.render_batch(self.fighters)

        self.gui.render_text(self.fps)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
