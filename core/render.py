"""Simple 2D OpenGL Rendering API

based on https://github.com/moderngl/moderngl/blob/master/examples/geometry_shader_sprites.py
"""

import pygame
import moderngl
import glm
import array

from typing import Optional, Tuple

from . import resources, particles


class Renderer2D:
    """Combines VBO, VAO and Shaders to render 2D sprites."""

    def __init__(self, context: moderngl.Context, cache: resources.Cache, max_num_sprites: int) -> None:
        """Initializes buffers for a maximum number of sprites."""
        self.context = context
        self.vbo = context.buffer(reserve=14 * 4 * max_num_sprites)

        self.program = context.program(vertex_shader=cache.get_shader('data/glsl/sprite.vert'),
                                       geometry_shader=cache.get_shader('data/glsl/sprite.geom'),
                                       fragment_shader=cache.get_shader('data/glsl/sprite.frag'))

        self.vao = context.vertex_array(self.program,
                                        [(self.vbo, '2f 2f 1f 4f 2f 2f 1f', 'in_position', 'in_size', 'in_rotation',
                                          'in_color', 'in_clip_offset', 'in_clip_size', 'in_brightness')])

        self.data = array.array('f')
        self.max_num_sprites = max_num_sprites
        self.num_sprites = 0

    def clear(self) -> None:
        """Resets the buffer data."""
        self.data = array.array('f')
        self.num_sprites = 0

    def render(self, texture: moderngl.Texture, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        """Renders the vertex data as points using the given texture, view matrix and projection matrix."""
        self.vbo.write(self.data)

        texture.use(0)
        self.program['view'].write(view_matrix)
        self.program['projection'].write(projection_matrix)
        self.program['sprite_texture'] = 0

        self.vao.render(mode=moderngl.POINTS, vertices=self.num_sprites)


# ----------------------------------------------------------------------------------------------------------------------


class Sprite:
    """Combines sprite data such as

    position: as pygame.math.Vector2, defaults to (0, 0)
    size: as pygame.math.Vector2, defaults to either the clipping size (if provided) or the texture size (fallback)
    rotation: as float in degree, defaults to 0
    color: as pygame.Color
    texture: as provided
    clip: as pygame.Rect in pixel coordinates
    brightness: as float, defaults to 1.0
    """

    def __init__(self, texture: moderngl.Texture, clip: Optional[pygame.Rect] = None):
        """Creates a sprite using a texture and an optional clipping rectangle."""
        self.center = pygame.math.Vector2(0, 0)
        self.scale = pygame.math.Vector2(1, 1)
        self.rotation = 0.0
        self.color = pygame.Color('white')
        self.brightness = 1.0
        self.clip = pygame.Rect(0, 0, *texture.size) if clip is None else clip
        self.texture = texture

    def as_tuple(self) -> Tuple[float, ...]:
        """Returns the sprite data as tuple, where color and clipping rect are normalized."""
        size = pygame.math.Vector2(self.clip.size).elementwise() * self.scale
        color = self.color.normalize()
        tex_size = pygame.math.Vector2(self.texture.size)
        clip_xy = pygame.math.Vector2(self.clip.topleft).elementwise() / tex_size
        clip_wh = pygame.math.Vector2(self.clip.size).elementwise() / tex_size
        return *self.center, *size, self.rotation, *color, *clip_xy, *clip_wh, self.brightness


# ----------------------------------------------------------------------------------------------------------------------


class TextureError(Exception):
    def __init__(self, expected: moderngl.Texture, found: moderngl.Texture) -> None:
        super().__init__(f'Unexpected texture: found {id(found)} but expected {id(expected)}')
        self.expected = expected
        self.found = found


class Batch:
    """Provides rendering multiple sprites at once. This requires all sprites to use the same texture."""

    def __init__(self, context: moderngl.Context, cache: resources.Cache, max_num_sprites: int) -> None:
        """Initializes the batch renderer for the given maximum number of sprites."""
        self.renderer = Renderer2D(context, cache, max_num_sprites)

        self.last_texture = None

    def clear(self) -> None:
        """Resets the renderer and the texture used."""
        self.renderer.clear()
        self.last_texture = None

    def append(self, sprite: Sprite) -> None:
        """Adds the sprite's data to the vertex array and saves the texture reference for later rendering.
        Throws an `TextureError` if the given sprite's texture does not the previous texture.
        """
        if self.last_texture is None:
            self.last_texture = sprite.texture

        if id(self.last_texture) != id(sprite.texture):
            raise TextureError(expected=self.last_texture, found=sprite.texture)

        self.renderer.data.extend(sprite.as_tuple())
        self.renderer.num_sprites += 1


# ----------------------------------------------------------------------------------------------------------------------


class Camera:
    """Provides a 2D orthographic camera with the potential of rendering single sprites or entire sprite batches.
    The camera can be modified using:

    center: as pygame.math.Vector2, defaults to (0, 0)
    rotation: as float in degree, defaults to 0
    """

    def __init__(self, context: moderngl.Context, cache: resources.Cache) -> None:
        """Creates the camera and sprite rendering capabilities."""
        self.renderer = Renderer2D(context, cache, 1)

        # set up camera
        self.center = pygame.math.Vector2(0, 0)
        self.rotation = 0.0
        self.zoom = 1.0

        self._up = glm.vec3(0, 1, 0)
        self._into = glm.vec3(0, 0, 1)
        self._screen_size = pygame.math.Vector2(pygame.display.get_window_size())

        self._m_view = self._get_view_matrix()
        self._m_proj = self._get_projection_matrix()

    def get_size(self) -> pygame.math.Vector2:
        return self._screen_size / self.zoom

    def get_rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, *self.get_size())
        rect.center = self.center.copy()
        return rect

    def _get_view_matrix(self) -> glm.mat4x4:
        """Return the view matrix (usually after camera moved)."""
        up_vector = glm.rotate(self._up, glm.radians(self.rotation), self._into)
        pos = glm.vec3(*self.center.xy, 1)
        return glm.lookAt(pos, pos - self._into, up_vector)

    def _get_projection_matrix(self) -> glm.mat4x4:
        """Return the projection matrix (usually once)."""
        size = self.get_size()
        return glm.ortho(-size[0] // 2, size[0] // 2, -size[1] // 2, size[1] // 2, 1, -1)

    def update(self) -> None:
        """Updates matrices after altering the camera or window size."""
        self._screen_size = pygame.math.Vector2(pygame.display.get_window_size())
        self._m_view = self._get_view_matrix()
        self._m_proj = self._get_projection_matrix()

    def render(self, sprite: Sprite) -> None:
        """Render the given sprite."""
        self.renderer.clear()
        self.renderer.data.extend(sprite.as_tuple())
        self.renderer.num_sprites = 1
        self.renderer.render(sprite.texture, self._m_view, self._m_proj)

    def render_batch(self, batch: Batch) -> None:
        """Render the given batch."""
        batch.renderer.render(batch.last_texture, self._m_view, self._m_proj)

    def render_particles(self, parts: particles.ParticleSystem) -> None:
        """Render the given particles."""
        parts.render(self._m_view, self._m_proj)


class GuiCamera(Camera):
    def __init__(self, context: moderngl.Context, cache: resources.Cache) -> None:
        super().__init__(context, cache)

    def _get_projection_matrix(self) -> glm.mat4x4:
        """Return the projection matrix (usually once)."""
        size = self.get_size()
        return glm.ortho(0, size[0], 0, size[1], 1, -1)
