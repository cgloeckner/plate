import moderngl
import pygame

import camera
import sprite


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

    # create sprites
    my_sprite = sprite.Sprite(context)
    my_sprite.texture = tex
    my_sprite.color = pygame.Color('blue')
    my_sprite.position.x = 0.5
    my_sprite.rotation = -25.3
    my_sprite.scale.x = 0.25
    my_sprite.scale.y = 0.25

    other_sprite = sprite.Sprite(context)
    other_sprite.texture = tex
    other_sprite.color = pygame.Color('red')
    other_sprite.position.x = -0.25
    other_sprite.position.y = -0.25
    other_sprite.rotation = 12.79
    other_sprite.scale.x = 0.5
    other_sprite.scale.y = 0.35

    cam = camera.Camera(window)
    cam.position.x = 0.25
    cam.position.y = -0.5
    cam.rotation = -22.0
    cam.update()

    max_fps = 600
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        context.clear(color=(0.08, 0.16, 0.18, 0.0))
        my_sprite.render(cam.m_view, cam.m_proj)
        other_sprite.render(cam.m_view, cam.m_proj)
        pygame.display.flip()

        clock.tick(max_fps)
        pygame.display.set_caption(f'{int(clock.get_fps())} FPS')

    pygame.quit()


if __name__ == '__main__':
    main()
