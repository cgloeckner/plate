import pygame
import moderngl
import glm
import random
import math

import render


def main() -> None:
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    size = (1600, 900)
    pygame.display.set_mode(size, flags=pygame.OPENGL | pygame.DOUBLEBUF)
    context = moderngl.create_context()
    context.enable(moderngl.BLEND)  # required for alpha stuff
    clock = pygame.time.Clock()

    surface = pygame.image.load('ship.png')
    tex0 = context.texture(size=surface.get_size(), components=4, data=pygame.image.tostring(surface, 'RGBA', True))
    tex0.filter = moderngl.NEAREST, moderngl.NEAREST
    surface = pygame.image.load('ufo.png')
    tex1 = context.texture(size=surface.get_size(), components=4, data=pygame.image.tostring(surface, 'RGBA', True))
    tex1.filter = moderngl.NEAREST, moderngl.NEAREST
    surface = pygame.image.load('tile.png')
    tex2 = context.texture(size=surface.get_size(), components=4, data=pygame.image.tostring(surface, 'RGBA', True))
    tex2.filter = moderngl.NEAREST, moderngl.NEAREST

    camera = render.Camera(context)

    s1 = render.Sprite(tex0, clip=pygame.Rect(0, 0, 32, 32))

    forward = pygame.math.Vector2(0, 1)
    right = pygame.math.Vector2(1, 0)

    s2 = render.Sprite(tex1, clip=pygame.Rect(0, 0, 32, 32))
    s2.center.y = 250

    batch = render.Batch(context, 50*50)
    for y in range(50):
        for x in range(50):
            s = render.Sprite(tex2)
            s.center.x = x * 64
            s.center.y = y * 64
            s.rotation = random.randrange(360)
            s.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))
            batch.append(s)

    max_fps = 600
    elapsed_ms = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            s1.center += right.rotate(s1.rotation) * -0.5 * elapsed_ms
        if keys[pygame.K_d]:
            s1.center += right.rotate(s1.rotation) * 0.5 * elapsed_ms
        if keys[pygame.K_s]:
            s1.center += forward.rotate(s1.rotation) * -0.5 * elapsed_ms
        if keys[pygame.K_w]:
            s1.center += forward.rotate(s1.rotation) * 0.5 * elapsed_ms
        if keys[pygame.K_q]:
            s1.rotation += 0.1 * elapsed_ms
        if keys[pygame.K_e]:
            s1.rotation -= 0.1 * elapsed_ms
        if keys[pygame.K_PLUS]:
            camera.zoom *= (1 + 0.001 * elapsed_ms)
            if camera.zoom > 5.0:
                camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            camera.zoom *= (1 - 0.001 * elapsed_ms)
            if camera.zoom < 0.1:
                camera.zoom = 0.1

        camera.center = s1.center.copy()
        camera.update()

        context.clear(color=(0.08, 0.16, 0.18, 0.0))
        camera.render_batch(batch)
        camera.render(s1)
        camera.render(s2)
        pygame.display.flip()

        elapsed_ms = clock.tick(max_fps)
        pygame.display.set_caption(f'{int(clock.get_fps())} FPS')

    pygame.quit()


if __name__ == '__main__':
    main()
