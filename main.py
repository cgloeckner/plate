import pygame
import moderngl
import math

import render
import app


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)

        surface = pygame.image.load('ship.png')
        self.tex0 = engine.context.texture(size=surface.get_size(), components=4,
                                           data=pygame.image.tostring(surface, 'RGBA', True))
        self.tex0.filter = moderngl.NEAREST, moderngl.NEAREST
        surface = pygame.image.load('ufo.png')
        self.tex1 = engine.context.texture(size=surface.get_size(), components=4,
                                           data=pygame.image.tostring(surface, 'RGBA', True))
        self.tex1.filter = moderngl.NEAREST, moderngl.NEAREST
        surface = pygame.image.load('tile.png')
        self.tex2 = engine.context.texture(size=surface.get_size(), components=4,
                                           data=pygame.image.tostring(surface, 'RGBA', True))
        self.tex2.filter = moderngl.NEAREST, moderngl.NEAREST

        self.camera = render.Camera(engine.context)

        self.s1 = render.Sprite(self.tex0, clip=pygame.Rect(0, 0, 32, 32))

        self.forward = pygame.math.Vector2(0, 1)
        self.right = pygame.math.Vector2(1, 0)

        self.s2 = render.Sprite(self.tex1, clip=pygame.Rect(0, 0, 32, 32))
        self.s2.center.y = 250

        self.total_ms = 0

        num_y = 50
        num_x = 100
        """
        self.batch = render.Batch(context, num_y * num_x)
        for y in range(num_y):
            for x in range(num_x):
                s = render.Sprite(tex2)
                s.center.x = x * 128
                s.center.y = y * 128
                s.scale.x = 2
                s.scale.y = 2
                s.rotation = random.randrange(360)
                s.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))
                self.batch.append(s)
        """
        self.tile = render.Sprite(self.tex2)
        self.tile.clip.w *= num_x
        self.tile.clip.h *= num_y

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.running = False

    def update(self, elapsed_ms) -> None:
        print(elapsed_ms)

        self.s1.scale.x = 1 + math.sin(self.total_ms / 250) * 0.05
        self.s1.scale.y = 1 + math.sin(self.total_ms / 250) * 0.05

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

        pygame.display.set_caption(f'{int(self.engine.clock.get_fps())} FPS')

    def render(self) -> None:
        self.camera.render(self.tile)
        self.camera.render(self.s1)
        self.camera.render(self.s2)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
