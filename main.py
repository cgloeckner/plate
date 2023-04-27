import moderngl
import pygame
import random
import math

import camera
import sprite


def random_sprite(ctx: moderngl.Context, texture: moderngl.Texture) -> sprite.Sprite:
    sprt = sprite.Sprite(ctx)
    sprt.texture = texture
    sprt.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))
    sprt.position.x = random.randrange(800)
    sprt.position.y = random.randrange(600)
    sprt.rotation = random.randrange(360)
    sprt.scale.x = random.randrange(150) + 50
    sprt.scale.y = random.randrange(150) + 50
    return sprt


def modify_sprite(s: sprite.Sprite, total_ms: int, elapsed_ms: int) -> None:
    s.rotation += elapsed_ms * 0.25
    s.scale.x += math.sin(total_ms) * 10
    s.scale.y += math.cos(total_ms) * 10
    s.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))


def main() -> None:
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    window = pygame.display.set_mode((800, 600), flags=pygame.OPENGL | pygame.DOUBLEBUF)
    context = moderngl.create_context()
    context.enable(moderngl.BLEND)  # required for alpha stuff
    clock = pygame.time.Clock()

    tex = sprite.texture_from_surface(context, pygame.image.load('ship.png'))
    tex.filter = moderngl.NEAREST, moderngl.NEAREST

    sprite_list = [random_sprite(context, tex) for i in range(350)]

    cam = camera.Camera()
    cam.position.x = 0.25
    cam.position.y = -0.5
    cam.rotation = -22.0
    cam.update()

    max_fps = 600
    elapsed_ms = 0
    total_ms = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        context.clear(color=(0.08, 0.16, 0.18, 0.0))

        for s in sprite_list:
            modify_sprite(s, total_ms, elapsed_ms)
            s.render(cam.m_view, cam.m_proj)

        pygame.display.flip()

        elapsed_ms = clock.tick(max_fps)
        total_ms += elapsed_ms
        pygame.display.set_caption(f'{int(clock.get_fps())} FPS')

    pygame.quit()


if __name__ == '__main__':
    main()
