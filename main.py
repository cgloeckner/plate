import moderngl
import pygame
import random
import math

import camera
import sprite


def random_sprite(ctx: moderngl.Context, texture: moderngl.Texture) -> sprite.Sprite:
    new_sprite = sprite.Sprite(ctx)
    new_sprite.texture = texture
    new_sprite.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))
    new_sprite.position.x = random.randrange(800)
    new_sprite.position.y = random.randrange(600)
    new_sprite.rotation = random.randrange(360)
    new_sprite.scale.x = random.randrange(150) + 50
    new_sprite.scale.y = random.randrange(150) + 50
    return new_sprite


def modify_sprite(existing_sprite: sprite.Sprite, total_ms: int, elapsed_ms: int) -> None:
    existing_sprite.rotation += elapsed_ms * 0.25
    existing_sprite.scale.x += math.sin(total_ms) * 10
    existing_sprite.scale.y += math.cos(total_ms) * 10
    existing_sprite.color = pygame.Color(random.randrange(255), random.randrange(255), random.randrange(255))


def main() -> None:
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    pygame.display.set_mode((800, 600), flags=pygame.OPENGL | pygame.DOUBLEBUF)
    context = moderngl.create_context()
    context.enable(moderngl.BLEND)  # required for alpha stuff
    clock = pygame.time.Clock()

    tex = sprite.texture_from_surface(context, pygame.image.load('ship.png'))
    tex.filter = moderngl.NEAREST, moderngl.NEAREST

    sprite_list = [random_sprite(context, tex) for _ in range(350)]

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
