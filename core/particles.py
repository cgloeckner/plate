"""Particle system that updates particles CPU-based and renders them GPU-based.
"""

import pygame
import moderngl
import numpy
import random
import glm

from typing import Tuple
from enum import IntEnum, auto

from . import resources


class Offset(IntEnum):
    """Provides offsets for accessing individual data within the ParticleSystem's array."""
    POS_X = 0
    POS_Y = auto()
    DIR_X = auto()
    DIR_Y = auto()
    SIZE = auto()
    SCALE = auto()
    COLOR_R = auto()
    COLOR_G = auto()
    COLOR_B = auto()


SPEED: float = 0.01
SHRINK: float = 0.0015
FADE_THRESHOLD: float = 0.05


class ParticleSystem:
    """Manages creating, updating and rendering lots of circular particles."""

    def __init__(self, context: moderngl.Context, cache: resources.Cache, max_num_particles: int,
                 resolution: float) -> None:
        """Create shader-based particle system with a given maximum number of particles, where each particle is a
        circle with the given texture resolution.
        """
        self._max_num_particles = max_num_particles
        self._data = numpy.zeros((max_num_particles, len(Offset)), dtype=numpy.float32)

        self._program = context.program(vertex_shader=cache.get_shader('data/glsl/particles.vert'),
                                        geometry_shader=cache.get_shader('data/glsl/particles.geom'),
                                        fragment_shader=cache.get_shader('data/glsl/particles.frag'))
        self._program['sprite_texture'] = 0

        self._vbo = context.buffer(self._data.tobytes())
        self._vao = context.vertex_array(self._program,
                                         [(self._vbo, '2f 2f 1f 1f 3f', 'in_position', 'in_direction', 'in_size',
                                          'in_scale', 'in_color')])

        # particle circle texture
        surface = pygame.Surface((resolution, resolution), flags=pygame.SRCALPHA)
        pygame.draw.circle(surface, pygame.Color('white'), (resolution//2, resolution//2), resolution//2)
        self._texture = resources.texture_from_surface(context, surface)

    def __len__(self) -> int:
        """Returns the number of particles that are currently in use."""
        return len(self._data)

    def emit(self, impact: pygame.math.Vector2, delta_degree: float, origin: pygame.math.Vector2,
             radius: float, speed: float, color: pygame.Color) -> None:
        """Emit a single particle using from the given data:

        Position: based on `origin`, randomly altered using the `radius`
        Direction: based on `impact`, randomly rotated to differ from `impact` by at least `delta_degree`, applied `speed`
        Radius: based on `radius`, randomly altered
        Color: based on `color`, normalized
        """
        angle = random.uniform(delta_degree, 360 - delta_degree)
        velocity = impact.rotate(angle) * random.uniform(0.01, 2 * speed)
        color_norm = color.normalize()[:-1]

        self._data.resize((self._data.shape[0] + 1, self._data.shape[1]), refcheck=False)
        index = self._data.shape[0] - 1

        self._data[index, Offset.POS_X] = origin.x + random.uniform(-radius, radius)
        self._data[index, Offset.POS_Y] = origin.y + random.uniform(-radius, radius)
        self._data[index, Offset.DIR_X] = velocity.x
        self._data[index, Offset.DIR_Y] = velocity.y
        self._data[index, Offset.SIZE] = radius
        self._data[index, Offset.SCALE] = 1 + random.random()
        self._data[index, Offset.COLOR_R] = color_norm[0]
        self._data[index, Offset.COLOR_G] = color_norm[1]
        self._data[index, Offset.COLOR_B] = color_norm[2]

    def update(self, elapsed_ms: int) -> None:
        """Updates all particles.

        Each particle is moved using its direction vector and is shrunk in scale. As the scale falls below a certain
        threshold, it is removed. The order of particles is not kept when particles are removed.
        """
        # update positions
        displacement = self._data[:, Offset.DIR_X:Offset.DIR_Y] * elapsed_ms * SPEED
        self._data[:, Offset.POS_X:Offset.POS_Y] += displacement

        # update scales
        # self._data[:, Offset.SCALE] *= (1 - SHRINK * elapsed_ms)
        scale_decay = numpy.exp(-SHRINK * elapsed_ms)
        self._data[:, Offset.SCALE] *= scale_decay

        # remove particles with scale below threshold
        self._data = self._data[self._data[:, Offset.SCALE] >= FADE_THRESHOLD]

    def render(self, view_matrix: glm.mat4x4, projection_matrix: glm.mat4x4) -> None:
        """Render the particles using the given view and projection matrices."""
        self._vbo.clear()
        self._vbo.write(self._data.tobytes())

        self._texture.use(0)
        self._program['view'].write(view_matrix)
        self._program['projection'].write(projection_matrix)

        self._vao.render(mode=moderngl.POINTS)
