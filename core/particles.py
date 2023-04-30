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
in float in_radius;
in vec4 in_color;

uniform mat4 view;
uniform mat4 projection;

out float radius;
out vec4 color;

void main() {
    gl_Position = projection * view * vec4(in_position, 0.0, 1.0);
    
    radius = in_radius;
    color = in_color;
}
"""

fragment_shader = """
#version 330

in float radius;
in vec4 color;

out vec4 frag_color;

void main() {
    frag_color = color;
}
"""


def create_particle(origin: pygame.math.Vector2, radius: float, color: pygame.Color) -> Tuple[float, ...]:
    """The particle starts at the given origin with a radius and a color, and is moved into a random direction.

    This normalizes the color.
    """
    x, y = origin
    x += random.random() * 2 * radius - 1
    y += random.random() * 2 * radius - 1
    direction = pygame.math.Vector2(0, 1).rotate(random.randrange(0, 360))
    direction *= random.random() * radius * 2 + 0.01
    color_tuple = color.normalize()
    return x, y, direction.x, direction.y, radius, *color_tuple


class ParticleSystem:
    def __init__(self, context: moderngl.Context, max_num_particles: int) -> None:
        self.context = context
        self.max_num_particles = max_num_particles

        self.vbo = context.buffer(reserve=9 * 4 * self.max_num_particles)
        self.program = context.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        self.vao = context.vertex_array(self.program,
                                        [(self.vbo, '2f 2f 1f 4f', 'in_position', 'in_direction', 'in_radius',
                                          'in_color')])

        self.data = array.array('f')
        self.num_particles = 0

    def emit(self, origin: pygame.math.Vector2, radius: float, color: pygame.Color, count: int = 1) -> None:
        for _ in range(count):
            self.data.extend(create_particle(origin, radius, color))
        self.num_particles += count

    def update(self, elapsed_ms: int) -> None:
        faded = array.array('I')
        for index in range(self.num_particles):
            self.data[index * 9] += self.data[index * 9 + 2] * elapsed_ms * 0.01
            self.data[index * 9 + 1] += self.data[index * 9 + 3] * elapsed_ms * 0.01
            self.data[index * 9 + 4] *= (1 - 0.001 * elapsed_ms)
            if self.data[index * 9 + 4] < 1.0:
                faded.append(index)

        # delete faded particles
        last_index = self.num_particles - 1
        for index in faded:
            for offset in range(9):
                self.data[index * 9 + offset] = self.data[last_index * 9 + offset]
            last_index -= 1
        self.num_particles = last_index + 1

    def render(self, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        self.vbo.write(self.data)

        self.program['view'].write(view_matrix)
        self.program['projection'].write(projection_matrix)

        self.vao.render(mode=moderngl.POINTS, vertices=self.num_particles)

