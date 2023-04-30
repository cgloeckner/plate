import pygame
import moderngl
import array
import random
import glm

from typing import Tuple


vertex_shader = """
#version 330

in vec2 in_position;
in vec2 in_direction;
in float in_size;
in float in_scale;
in vec4 in_color;

uniform mat4 view;
uniform mat4 projection;

uniform sampler2D sprite_texture;

out float size;
out float scale;
out vec4 color;

void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    
    size = in_size;
    scale = in_scale;
    color = in_color;
}
"""

geometry_shader = """
#version 330

layout (points) in;
layout (triangle_strip, max_vertices = 4) out;

in float size[];
in float scale[];
in vec4 color[];

uniform mat4 view;
uniform mat4 projection;
uniform sampler2D sprite_texture;

out float out_scale;
out vec2 uv;
out vec4 v_color;

void main() {
    vec2 center = gl_in[0].gl_Position.xy;
    float step = size[0] * scale[0] / 2;

    // Upper left
    gl_Position = projection * view * vec4(vec2(-step, step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(0.0, 1.0);
    v_color = color[0];
    EmitVertex();

    // lower left
    gl_Position = projection * view * vec4(vec2(-step, -step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(0.0, 0.0);
    v_color = color[0];
    EmitVertex();

    // upper right
    gl_Position = projection * view * vec4(vec2(step, step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(1.0, 1.0);
    v_color = color[0];
    EmitVertex();

    // lower right
    gl_Position = projection * view * vec4(vec2(step, -step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(1.0, 0.0);
    v_color = color[0];
    EmitVertex();

    EndPrimitive();
}
"""

fragment_shader = """
#version 330

in float scale;
in vec2 uv;
in vec4 v_color;

uniform sampler2D sprite_texture;

out vec4 frag_color;

void main() {
    float f_scale = scale;
    if (f_scale > 1.0) {
        f_scale = 1.0;
    }
    if (f_scale < 0.0) {
        f_scale = 0.0;
    }
    vec4 tex_color = v_color * texture(sprite_texture, uv);
    vec3 color = tex_color.rgb * tex_color.a;
    frag_color = vec4(color, 1.0 - f_scale);
}
"""


def create_particle(origin: pygame.math.Vector2, radius: float, speed: float, color: pygame.Color) -> Tuple[float, ...]:
    """The particle starts at the given origin with a radius and a color, and is moved into a random direction.

    This normalizes the color.
    """
    x, y = origin
    x += random.random() * 2 * radius - 1
    y += random.random() * 2 * radius - 1
    direction = pygame.math.Vector2(0, 1).rotate(random.randrange(0, 360))
    direction *= random.random() * speed * 2 + 0.01
    color_tuple = color.normalize()
    return x, y, direction.x, direction.y, radius, 1.0, *color_tuple


class ParticleSystem:
    def __init__(self, context: moderngl.Context, max_num_particles: int, resolution: float) -> None:
        self.context = context
        self.max_num_particles = max_num_particles

        self.vbo = context.buffer(reserve=9 * 4 * self.max_num_particles)
        self.program = context.program(vertex_shader=vertex_shader, geometry_shader=geometry_shader,
                                       fragment_shader=fragment_shader)
        self.program['sprite_texture'] = 0
        self.vao = context.vertex_array(self.program,
                                        [(self.vbo, '2f 2f 1f 1f 4f', 'in_position', 'in_direction', 'in_size',
                                          'in_scale', 'in_color')])

        # particle circle texture
        surface = pygame.Surface((resolution, resolution), flags=pygame.SRCALPHA)
        pygame.draw.circle(surface, pygame.Color('white'), (resolution//2, resolution//2), resolution//2)
        img_data = pygame.image.tostring(surface, 'RGBA', True)
        self.texture = self.context.texture(size=surface.get_size(), components=4, data=img_data)

        self.data = array.array('f')
        self.num_particles = 0

    def emit(self, origin: pygame.math.Vector2, radius: float, speed: float, color: pygame.Color,
             count: int = 1) -> None:
        for _ in range(count):
            self.data.extend(create_particle(origin, radius, speed, color))
        self.num_particles += count

    def get_particle_count(self) -> int:
        return self.num_particles

    def update(self, elapsed_ms: int) -> None:
        # update all particles
        faded_indices = array.array('I')
        for index in range(self.num_particles):
            self.data[index * 10] += self.data[index * 10 + 2] * elapsed_ms * 0.01
            self.data[index * 10 + 1] += self.data[index * 10 + 3] * elapsed_ms * 0.01
            self.data[index * 10 + 5] *= (1 - 0.0015 * elapsed_ms)
            if self.data[index * 10 + 5] < 0.05:
                # mark particle as faded
                faded_indices.append(index)

        # delete faded particles
        last_index = self.num_particles - 1
        for index in faded_indices:
            for offset in range(10):
                self.data[index * 10 + offset] = self.data[last_index * 10 + offset]
            last_index -= 1
        self.num_particles = last_index + 1
        for _ in range(len(faded_indices) * 10):
            self.data.pop()

    def render(self, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        self.vbo.write(self.data)

        self.texture.use(0)
        self.program['view'].write(view_matrix)
        self.program['projection'].write(projection_matrix)

        self.vao.render(mode=moderngl.POINTS, vertices=self.num_particles)

