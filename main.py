import pygame
import pygame.gfxdraw
import moderngl
import random
import numpy

from core import app, resources, particles, render, sprite, text
import game


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.scene = game.Scene(engine)

        self.physics = game.PhysicsSystem(self.scene, self.on_collision)
        self.controls = game.ControlsSystem(self.scene)
        self.renderer = game.RendererSystem(self.scene)

        self.total_ms = 0
        self.fps = text.Text(self.engine.context, self.engine.cache.get_font(font_size=30))
        self.perf = text.Text(self.engine.context, self.engine.cache.get_font(font_size=24))

        # create asteroids
        for _ in range(1_000):
            s = sprite.Sprite(self.renderer.asteroids.get_texture())
            s.center.x = random.randrange(0, 1600 * 10)
            s.center.y = random.randrange(0, 900 * 10)
            s.rotation = random.uniform(0.0, 360.0)
            s.scale *= random.uniform(0.5, 4.0) / 10
            s.velocity = pygame.math.Vector2(0, 1).rotate(random.uniform(0.0, 360.0)) * random.uniform(0.5, 4.0)
            s.velocity *= 0.05
            self.scene.asteroids.add(s)

        # create spacecrafts
        s = sprite.Sprite(self.renderer.spacecrafts.get_texture(), clip=pygame.Rect(0, 0, 32, 32))
        s.center.x = 8000
        s.center.y = 4500
        self.scene.spacecrafts.add(s)

        for i in range(150):
            s = sprite.Sprite(self.renderer.spacecrafts.get_texture(), clip=pygame.Rect(0, 0, 32, 32))
            s.center.x += 200 + i * 50
            s.center.y += 200 + i * 50
            s.color = pygame.Color('red')
            s.color.a = 96
            self.scene.spacecrafts.add(s)

    def on_collision(self, index1: int, type1: game.ObjectType, index2: int, type2: game.ObjectType) -> None:
        #print('collision', index1, type1, index2, type2)
        pass

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            enable = not self.asteroids.has_enabled_bounding_circles()
            self.asteroids.enable_bounding_circles(enable)
            self.fighters.enable_bounding_circles(enable)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.camera.to_world_pos(pygame.math.Vector2(pygame.mouse.get_pos()))
            indices = self.camera.query_visible(self.asteroids.sprites.data)

            # query at which asteroids the user clicked
            clicked = list()
            for i in indices:
                x, y = self.asteroids.sprites.data[i, sprite.Offset.POS_X:sprite.Offset.POS_Y+1]
                p = pygame.math.Vector2(x, y)
                r = self.asteroids.sprites.data[i, sprite.Offset.SIZE_X] // 2
                if p.distance_squared_to(pos) <= r ** 2:
                    # click on asteroid!
                    clicked.append(i)

            # traverse backwards to avoid index invalidation
            for index in reversed(clicked):
                x, y = self.asteroids.sprites.data[index, sprite.Offset.POS_X:sprite.Offset.POS_Y+1]
                dx, dy = self.asteroids.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1]
                size = max(self.asteroids.sprites.data[index, sprite.Offset.SIZE_X:sprite.Offset.SIZE_Y+1])
                for _ in range(100):
                    self.parts.emit(origin=pygame.math.Vector2(x, y),
                                    radius=size,
                                    color=pygame.Color('blue'),
                                    impact=pygame.math.Vector2(dx, dy))
                self.asteroids.hit_asteroid(index)
        """

    def update(self, elapsed_ms) -> None:
        with self.engine.perf_monitor:
            self.engine.perf_monitor('controls')
            self.controls.update(elapsed_ms)

        with self.engine.perf_monitor:
            self.engine.perf_monitor('physics')
            self.physics.update(elapsed_ms)

        with self.engine.perf_monitor:
            self.engine.perf_monitor('particles')
            self.scene.particles.update(elapsed_ms)

        with self.engine.perf_monitor:
            self.engine.perf_monitor('camera')

            # let camera follow player
            self.scene.camera.center = pygame.math.Vector2(
                *self.scene.spacecrafts.data[0, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
            self.scene.camera.rotation = self.scene.spacecrafts.data[0, sprite.Offset.ROTATION]

            self.scene.camera.update()

        self.total_ms += elapsed_ms
        num_fps = int(self.engine.clock.get_fps())
        if self.total_ms > 100:
            self.fps.set_string(f'FPS: {num_fps}')
            self.perf.set_string(str(self.engine.perf_monitor))
            self.perf.sprite.center.y = pygame.display.get_window_size()[1]
            self.perf.sprite.origin.y = 1.0
            self.total_ms -= 100

    def render(self) -> None:
        self.renderer.render()

        self.scene.gui.render_text(self.fps)
        self.scene.gui.render_text(self.perf)y


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
