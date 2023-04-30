import moderngl
import array
import random
import glm


vertex_shader = """
#version 330

in vec2 in_position;
in vec2 in_direction;  // not used atm

uniform mat4 view;
uniform mat4 projection;

void main() {
    gl_Position = projection * view * vec4(in_position, 0.0, 1.0);
}
"""

fragment_shader = """
#version 330

out vec4 frag_color;

void main() {
    frag_color = vec4(1.0, 1.0, 1.0, 1.0);
}
"""


class ParticleSystem:
    def __init__(self, context: moderngl.Context, max_num_particles: int) -> None:
        self.context = context
        self.max_num_particles = max_num_particles

        self.vbo = context.buffer(reserve=4 * 4 * self.max_num_particles)
        self.program = context.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        self.vao = context.vertex_array(self.program, [(self.vbo, '2f 2f', 'in_position', 'in_direction')])

        self.data = array.array('f')
        for _ in range(self.max_num_particles):
            # random position
            self.data.append(random.randrange(1600) - 800)
            self.data.append(random.randrange(900) - 450)
            self.data.append(random.random() * 2 - 1)
            self.data.append(random.random() * 2 - 1)

    def update(self, elapsed_ms: int) -> None:
        for index in range(self.max_num_particles):
            self.data[index * 4] += self.data[index * 4 + 2] * elapsed_ms * 0.01
            self.data[index * 4 + 1] += self.data[index * 4 + 3] * elapsed_ms * 0.01

    def render(self, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        self.vbo.write(self.data)

        self.program['view'].write(view_matrix)
        self.program['projection'].write(projection_matrix)

        self.vao.render(mode=moderngl.POINTS, vertices=self.max_num_particles)

