"""Simple 2D OpenGL Rendering API

based on https://github.com/moderngl/moderngl/blob/master/examples/geometry_shader_sprites.py
"""

import pygame
import moderngl
import glm
import array

from typing import Optional, Tuple
from enum import IntEnum

from . import resources, particles


class Sprite:
    """Combines sprite data such as

    position: as pygame.math.Vector2, defaults to (0, 0)
    scale: as pygame.math.Vector2, defaults to either the clipping size (if provided) or the texture size (fallback)
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


class Offset(IntEnum):
    """Provides offsets for accessing individual data within the RenderBatch's array."""
    POS_X = 0
    POS_Y = 1
    SIZE_X = 2
    SIZE_Y = 3
    ROTATION = 4
    COLOR_R = 5
    COLOR_G = 6
    COLOR_B = 7
    COLOR_A = 8
    CLIP_X = 9
    CLIP_Y = 10
    CLIP_W = 11
    CLIP_H = 12
    BRIGHTNESS = 13


# ----------------------------------------------------------------------------------------------------------------------


class TextureError(Exception):
    def __init__(self, expected: moderngl.Texture, found: moderngl.Texture) -> None:
        super().__init__(f'Unexpected texture: found {id(found)} but expected {id(expected)}')
        self.expected = expected
        self.found = found


# ----------------------------------------------------------------------------------------------------------------------


class RenderBatch:
    """Combines VBO, VAO and Shaders to render 2D sprites.

    If multiple sprites are appended, they need to use the same texture.

    The data array is publicly available to allow for in place manipulation (e.g. interpolating positions).
    """

    def __init__(self, context: moderngl.Context, cache: resources.Cache, max_num_sprites: int) -> None:
        """Initializes buffers for a maximum number of sprites."""
        self._context = context
        self._vbo = context.buffer(reserve=len(Offset) * 4 * max_num_sprites)

        self._program = context.program(vertex_shader=cache.get_shader('data/glsl/sprite.vert'),
                                        geometry_shader=cache.get_shader('data/glsl/sprite.geom'),
                                        fragment_shader=cache.get_shader('data/glsl/sprite.frag'))

        self._vao = context.vertex_array(self._program,
                                         [(self._vbo, '2f 2f 1f 4f 2f 2f 1f', 'in_position', 'in_size', 'in_rotation',
                                           'in_color', 'in_clip_offset', 'in_clip_size', 'in_brightness')])

        self._max_num_sprites = max_num_sprites
        self._num_sprites = 0
        self._texture = None
        self.data = array.array('f')

    def clear(self) -> None:
        """Resets the buffer data."""
        self._num_sprites = 0
        self._texture = None
        self.data = array.array('f')

    def __len__(self) -> int:
        """Returns the number of sprites that were appended to the renderer."""
        return self._num_sprites

    def get_texture(self) -> moderngl.Texture:
        """Returns the texture that is bound to the renderer batch."""
        return self._texture

    def append(self, sprite: Sprite) -> None:
        """Adds the sprite's data to the vertex array and saves the texture reference for later rendering.
        Throws an `TextureError` if the given sprite's texture does not the previous texture.
        """
        if self._texture is None:
            self._texture = sprite.texture

        if id(self._texture) != id(sprite.texture):
            raise TextureError(expected=self._texture, found=sprite.texture)

        self._num_sprites += 1
        self.data.extend(sprite.as_tuple())

    def render(self, texture: moderngl.Texture, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        """Renders the vertex data as points using the given texture, view matrix and projection matrix."""
        self._vbo.write(self.data)

        texture.use(0)
        self._program['view'].write(view_matrix)
        self._program['projection'].write(projection_matrix)
        self._program['sprite_texture'] = 0

        self._vao.render(mode=moderngl.POINTS, vertices=self._num_sprites)


# ----------------------------------------------------------------------------------------------------------------------


class Camera:
    """Provides a 2D orthographic camera with the potential of rendering single sprites or entire sprite batches.
    The camera can be modified using:

    center: as pygame.math.Vector2, defaults to (0, 0)
    rotation: as float in degree, defaults to 0
    zoom: as float, defaults to 1
    """

    def __init__(self, context: moderngl.Context, cache: resources.Cache) -> None:
        """Creates the camera and sprite rendering capabilities."""
        self._renderer = RenderBatch(context, cache, 1)

        self.center = pygame.math.Vector2(0, 0)
        self.rotation = 0.0
        self.zoom = 1.0

        self._up = glm.vec3(0, 1, 0)
        self._into = glm.vec3(0, 0, 1)
        self._screen_size = pygame.math.Vector2(pygame.display.get_window_size())

        self._m_view = self._get_view_matrix()
        self._m_proj = self._get_projection_matrix()

    def get_size(self) -> pygame.math.Vector2:
        """Returns the size of the zoomed viewport."""
        return self._screen_size / self.zoom

    def get_rect(self) -> pygame.Rect:
        """Returns a rectangle that describes the visible area."""
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
        self._renderer.clear()
        self._renderer.append(sprite)
        self._renderer.render(sprite.texture, self._m_view, self._m_proj)

    def render_batch(self, batch: RenderBatch) -> None:
        """Render the given batch."""
        batch.render(batch.get_texture(), self._m_view, self._m_proj)

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
