import moderngl
import numpy
import pygame


# FIXME: load from data/glsl/light.vert and data/glsl/light.frag
def create_lightmap(context: moderngl.Context, radius: int) -> moderngl.Texture:
    vert = '''
    #version 330

    in vec2 in_vert;
    in vec2 in_texcoord;

    out vec2 texcoord;

    void main() {
        gl_Position = vec4(in_vert, 0.0, 1.0);
        texcoord = in_texcoord;
    }
'''

    frag = '''
    #version 330

    uniform vec2 center;
    uniform float radius;
    uniform vec4 color;

    in vec2 texcoord;
    out vec4 out_color;

    void main() {
        float dist = distance(texcoord, center);
        float intensity = exp(-6.0 * dist / radius);
        vec3 tmp_color = color.xyz * intensity;
        out_color = vec4(tmp_color, color.a * intensity);
    }
'''

    prog = context.program(vertex_shader=vert, fragment_shader=frag)

    vertices = numpy.array([
        # x, y, u, v
        -1.0, -1.0, 0.0, 0.0,
        1.0, -1.0, 1.0, 0.0,
        1.0, 1.0, 1.0, 1.0,
        -1.0, 1.0, 0.0, 1.0,
    ])

    vbo = context.buffer(vertices.astype('f4').tobytes())
    vao = context.vertex_array(prog, [(vbo, '2f 2f', 'in_vert', 'in_texcoord')])

    size = (2 * radius, 2 * radius)
    texture = context.texture(size, 4)
    fbo = context.framebuffer(color_attachments=[texture])

    prog['center'].value = (0.5, 0.5)
    prog['radius'].value = 1.0
    prog['color'].value = pygame.Color('white').normalize()

    fbo.use()
    context.clear(0.0, 0.0, 0.0, 0.0)
    vao.render(mode=moderngl.TRIANGLE_FAN)
    context.screen.use()

    #data = numpy.frombuffer(texture.read(), dtype=numpy.uint8).reshape(*size, 4)
    #surface = pygame.image.frombuffer(data, size, 'RGBA')
    #pygame.image.save(surface, '/tmp/output.png')

    return texture
