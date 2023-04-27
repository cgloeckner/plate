import pygame
import moderngl
import numpy
import glm


vertex_shader = """
#version 330 core

layout (location = 0) in vec2 in_texcoord_0;
layout (location = 1) in vec3 in_position;

out vec2 uv_0;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

void main() {
    uv_0 = in_texcoord_0;
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
}"""


fragment_shader = """
#version 330 core

layout (location = 0) out vec4 frag_color;

in vec2 uv_0;

uniform sampler2D u_texture_0;
uniform vec4 v_color;

void main() { 
    vec4 tex_color = v_color * texture(u_texture_0, uv_0);
    vec3 color = tex_color.rgb * tex_color.a;
    frag_color = vec4(color, tex_color.a);
}"""


def texture_from_surface(context: moderngl.Context, surface: pygame.Surface) -> moderngl.Texture:
    """Create texture from a surface."""
    return context.texture(size=surface.get_size(), components=4, data=pygame.image.tostring(surface, 'RGBA', True))


# create vertices
def build_vertices(vertices_array, indices_array) -> numpy.array:
    """Builds vertex data in a suitable format."""
    data = [vertices_array[ind] for triangle in indices_array for ind in triangle]
    return numpy.array(data, dtype='f4')


class Sprite:
    def __init__(self, ctx: moderngl.Context):
        self.position = pygame.Vector2(0.0, 0.0)
        self.rotation = 0.0
        self.scale = pygame.Vector2(1.0, 1.0)
        self.color = pygame.Color('white')
        self.texture = None

        # order: top left, top right, bottom right, bottom left
        vertices = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0)]
        tex_coord = [(0, 0), (1, 0), (1, 1), (0, 1)]

        indices = [(0, 1, 2), (0, 2, 3)]
        vertex_data = build_vertices(vertices, indices)
        tex_coord_data = build_vertices(tex_coord, indices)
        vertex_data = numpy.hstack([tex_coord_data, vertex_data])

        self._vbo = ctx.buffer(vertex_data)
        self._shader = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        self._shader['u_texture_0'] = 0
        self._vao = ctx.vertex_array(self._shader, [(self._vbo, '2f 3f', 'in_texcoord_0', 'in_position')])

    def __del__(self):
        self._shader.release()
        self._vbo.release()
        self._vao.release()

    def _get_transform(self) -> glm.mat4x4:
        """Returns the model transformation matrix."""
        m_model = glm.translate(glm.mat4(), glm.vec3(*self.position, 0))
        m_model *= glm.rotate(glm.mat4(), glm.radians(self.rotation), glm.vec3(0, 0, 1))
        m_model *= glm.scale(glm.mat4(), glm.vec3(self.scale.x, self.scale.y, 1.0))
        return m_model

    def render(self, m_view: glm.mat4x4, m_proj: glm.mat4x4) -> None:
        """Renders the sprite using the given view and projection matrices."""
        if self.texture is None:
            return

        self.texture.use()
        self._shader['m_model'].write(self._get_transform())
        self._shader['m_view'].write(m_view)
        self._shader['m_proj'].write(m_proj)
        self._shader['v_color'] = self.color.normalize()

        self._vao.render()
