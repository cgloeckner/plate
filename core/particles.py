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
    v_color = color[0];
    
    vec2 center = gl_in[0].gl_Position.xy;
    float step = size[0] * scale[0] / 2;

    // Upper left
    gl_Position = projection * view * vec4(vec2(-step, step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(0.0, 1.0);
    EmitVertex();

    // lower left
    gl_Position = projection * view * vec4(vec2(-step, -step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(0.0, 0.0);
    EmitVertex();

    // upper right
    gl_Position = projection * view * vec4(vec2(step, step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(1.0, 1.0);
    EmitVertex();

    // lower right
    gl_Position = projection * view * vec4(vec2(step, -step) + center, 0.0, 1.0);
    out_scale = scale[0];
    uv = vec2(1.0, 0.0);
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
    vec4 tex_color = v_color * texture(sprite_texture, uv);
    frag_color = vec4(tex_color.rgb, 1.0 - clamp(scale, 0.0, 1.0));
}
"""


def random_particle(impact: pygame.math.Vector2, delta_degree: float, origin: pygame.math.Vector2, radius: float,
                    speed: float, color: pygame.Color) -> Tuple[float, ...]:
    """Creates a tuple with particle data in the following order:

    Position: based on `origin`, randomly altered using the `radius`
    Direction: based on `impact`, randomly rotated to differ from `impact` by at least `delta_degree`, applied `speed`
    Radius: based on `radius`, randomly altered
    Color: based on `color`, normalized
    """
    x, y = origin
    x += random.random() * 2 * radius - 1
    y += random.random() * 2 * radius - 1

    angle = random.uniform(delta_degree, 360-delta_degree)
    direction = impact.rotate(angle)
    direction *= random.uniform(0.01, 2 * speed)

    color_tuple = color.normalize()

    return x, y, direction.x, direction.y, radius, 1 + random.random(), *color_tuple


class ParticleSystem:
    """Manages creating, updating and rendering lots of circular particles."""

    def __init__(self, context: moderngl.Context, max_num_particles: int, resolution: float) -> None:
        """Create shader-based particle system with a given maximum number of particles, where each particle is a
        circle with the given texture resolution.
        """
        self._max_num_particles = max_num_particles

        self._vbo = context.buffer(reserve=9 * 4 * self._max_num_particles)
        self._program = context.program(vertex_shader=vertex_shader, geometry_shader=geometry_shader,
                                        fragment_shader=fragment_shader)
        self._program['sprite_texture'] = 0
        self._vao = context.vertex_array(self._program,
                                         [(self._vbo, '2f 2f 1f 1f 4f', 'in_position', 'in_direction', 'in_size',
                                          'in_scale', 'in_color')])

        # particle circle texture
        surface = pygame.Surface((resolution, resolution), flags=pygame.SRCALPHA)
        pygame.draw.circle(surface, pygame.Color('white'), (resolution//2, resolution//2), resolution//2)
        img_data = pygame.image.tostring(surface, 'RGBA', True)
        self._texture = context.texture(size=surface.get_size(), components=4, data=img_data)

        self._data = array.array('f')
        self._num_particles = 0

    def emit(self, count: int, *args) -> None:
        """Emit a given number of particles using data in `*args`, forwarded to `random_particle`."""
        for _ in range(count):
            self._data.extend(random_particle(*args))
        self._num_particles += count

    def get_particle_count(self) -> int:
        """Returns the number of particles that are currently in use."""
        return self._num_particles

    def update(self, elapsed_ms: int) -> None:
        """Updates all particles.

        Each particle is moved using its direction vector and is shrunk in scale. As the scale falls below a certain
        threshold, it is removed. The order of particles is not kept when particles are removed.
        """
        # update all particles
        faded_indices = array.array('I')
        for index in range(self._num_particles):
            self._data[index * 10] += self._data[index * 10 + 2] * elapsed_ms * 0.01
            self._data[index * 10 + 1] += self._data[index * 10 + 3] * elapsed_ms * 0.01
            self._data[index * 10 + 5] *= (1 - 0.0015 * elapsed_ms)
            if self._data[index * 10 + 5] < 0.05:
                # mark particle as faded
                faded_indices.append(index)

        # delete faded particles
        last_index = self._num_particles - 1
        for index in faded_indices:
            for offset in range(10):
                self._data[index * 10 + offset] = self._data[last_index * 10 + offset]
            last_index -= 1
        self._num_particles = last_index + 1
        for _ in range(len(faded_indices) * 10):
            self._data.pop()

    def render(self, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        """Render the particles using the given view and projection matrices."""
        self._vbo.write(self._data)

        self._texture.use(0)
        self._program['view'].write(view_matrix)
        self._program['projection'].write(projection_matrix)

        self._vao.render(mode=moderngl.POINTS, vertices=self._num_particles)

