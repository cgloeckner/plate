"""Simple 2D OpenGL Rendering API

based on https://github.com/moderngl/moderngl/blob/master/examples/geometry_shader_sprites.py
"""
import numpy
import pygame
import moderngl
import glm

from . import resources, particles, sprite, text


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

    def __init__(self, context: moderngl.Context, cache: resources.Cache, max_num_sprites: int,
                 sprite_array: sprite.SpriteArray) -> None:
        """Initializes buffers for a maximum number of sprites."""
        self._context = context
        self._max_num_sprites = max_num_sprites

        self._vbo = context.buffer(reserve=len(sprite.Offset) * 4 * max_num_sprites, dynamic=True)
        self._program = context.program(vertex_shader=cache.get_shader('data/glsl/sprite.vert'),
                                        geometry_shader=cache.get_shader('data/glsl/sprite.geom'),
                                        fragment_shader=cache.get_shader('data/glsl/sprite.frag'))
        self._vao = context.vertex_array(self._program,
                                         [(self._vbo, '2f 2f 2f 2f 1f 4f 2f 2f 1f', 'in_position', 'in_velocity',
                                           'in_origin', 'in_size', 'in_rotation', 'in_color',
                                           'in_clip_offset', 'in_clip_size', 'in_brightness')])

        self._num_sprites = 0
        self._texture = None
        self._alt_texture = None
        self._data = sprite_array
        self._show_bounding_circles = False

    def clear(self) -> None:
        """Resets the buffer data."""
        self._num_sprites = 0
        self._texture = None
        self._data.clear()

    def __len__(self) -> int:
        """Returns the number of sprites that were appended to the renderer."""
        return self._num_sprites

    def get_texture(self) -> moderngl.Texture:
        """Returns the texture that is bound to the renderer batch."""
        return self._alt_texture if self._show_bounding_circles else self._texture

    def add(self, s: sprite.Sprite) -> None:
        """Adds the sprite's data to the vertex array and saves the texture reference for later rendering.
        Throws an `TextureError` if the given sprite's texture does not the previous texture.
        """
        if self._texture is None:
            self._texture = s.texture

        if id(self._texture) != id(s.texture):
            raise TextureError(expected=self._texture, found=s.texture)

        self._num_sprites += 1
        self._data.add(s)

    def has_enabled_bounding_circles(self) -> bool:
        return self._show_bounding_circles

    def enable_bounding_circles(self, show_bounding_circles: bool) -> None:
        self._show_bounding_circles = show_bounding_circles

        if show_bounding_circles and self._alt_texture is None:
            # create copy of texture
            w, h = self._texture.size
            surface = pygame.image.frombuffer(self._texture.read(), (w, h), 'RGBA')

            # draw circle over the first square frame (assuming it's a single row frame sheet)
            radius = h // 2
            pygame.gfxdraw.circle(surface, radius, radius, radius - 1, pygame.Color('red'))
            pygame.image.save(surface, '/tmp/out.png')

            # store as alternative texture
            self._alt_texture = resources.texture_from_surface(self._context, surface, False)
            self._alt_texture.filter = moderngl.NEAREST, moderngl.NEAREST

    def render(self, texture: moderngl.Texture, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        """Renders the vertex data as points using the given texture, view matrix and projection matrix."""
        self._vbo.write(self._data.to_bytes())

        texture.use(0)
        self._program['view'].write(view_matrix)
        self._program['projection'].write(projection_matrix)
        self._program['sprite_texture'] = 0

        self._vao.render(mode=moderngl.POINTS)


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
        self._data = sprite.SpriteArray()
        self._renderer = RenderBatch(context, cache, 1, self._data)

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

    def get_bounding_rect(self) -> pygame.FRect:
        """Returns a rectangle that contains the visible in-game area, enlarged so that even rotation is caught."""
        w, h = self.get_size()
        diagonal = (w ** 2 + h ** 2) ** 0.5
        rect = pygame.FRect(0, 0, diagonal, diagonal)
        rect.center = self.center
        return rect

    def query_visible(self, data: numpy.ndarray) -> numpy.ndarray:
        """Query visible elements from the given array using an enlarged bounding rectangle."""
        rect = self.get_bounding_rect()
        return numpy.where(
            (rect.left <= data[:, sprite.Offset.POS_X]) & (data[:, sprite.Offset.POS_X] <= rect.right) &
            (rect.top <= data[:, sprite.Offset.POS_Y]) & (data[:, sprite.Offset.POS_Y] <= rect.bottom)
        )[0]

    def to_world_pos(self, screen_pos: pygame.math.Vector2) -> pygame.math.Vector2:
        """Transforms the position into a world position."""
        window_size = pygame.math.Vector2(pygame.display.get_window_size())
        screen_pos.y = window_size.y - screen_pos.y
        pos = (screen_pos - window_size / 2) / self.zoom
        return pos.rotate(self.rotation) + self.center

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

    def render(self, s: sprite.Sprite) -> None:
        """Render the given sprite."""
        self._renderer.clear()
        self._renderer.add(s)
        self._renderer.render(s.texture, self._m_view, self._m_proj)

    def render_text(self, t: text.Text) -> None:
        if t.sprite is None:
            return

        self._renderer.clear()
        self._renderer.add(t.sprite)
        self._renderer.render(t.sprite.texture, self._m_view, self._m_proj)

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
