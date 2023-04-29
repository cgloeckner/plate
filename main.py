import pygame
import moderngl
import glm
import random
import math

import render


def random_sprite(texture: moderngl.Texture) -> render.Sprite:
    size = pygame.display.get_window_size()

    new_sprite = render.Sprite(texture, pygame.Rect(0, 0, 32, 32))
    new_sprite.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))
    new_sprite.pos.x = random.randrange(size[0])
    new_sprite.pos.y = random.randrange(size[1])
    new_sprite.rotation = random.randrange(360)
    new_sprite.size.x = random.randrange(150) + 50
    new_sprite.size.y = random.randrange(150) + 50
    return new_sprite


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
    surface = pygame.image.load('ufo.png')
    tex1 = context.texture(size=surface.get_size(), components=4, data=pygame.image.tostring(surface, 'RGBA', True))
    surface = pygame.image.load('tile.png')
    tex2 = context.texture(size=surface.get_size(), components=4, data=pygame.image.tostring(surface, 'RGBA', True))

    camera = render.Camera(context)

    s1 = render.Sprite(tex0, clip=pygame.Rect(0, 0, 32, 32))
    s1.pos.x = size[0] // 2
    s1.pos.y = size[1] // 2

    s2 = render.Sprite(tex1, clip=pygame.Rect(0, 0, 32, 32))
    s2.pos.x = size[0] // 2
    s2.pos.y = size[1] // 4 * 3

    sprites = [random_sprite(tex2) for _ in range(3000)]

    batch = render.Batch(context, len(sprites))
    for s in sprites:
        batch.append(s)

    max_fps = 600
    elapsed_ms = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        camera.update()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            camera.position.x -= 0.25 * elapsed_ms
        if keys[pygame.K_d]:
            camera.position.x += 0.25 * elapsed_ms
        if keys[pygame.K_s]:
            camera.position.y -= 0.25 * elapsed_ms
        if keys[pygame.K_w]:
            camera.position.y += 0.25 * elapsed_ms
        if keys[pygame.K_q]:
            camera.rotation += 0.1 * elapsed_ms
        if keys[pygame.K_e]:
            camera.rotation -= 0.1 * elapsed_ms

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
