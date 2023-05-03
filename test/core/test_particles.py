import unittest
import pygame
import moderngl
import glm

from core import resources, particles


class ParticlesTest(unittest.TestCase):

    def setUp(self):
        self.ctx = moderngl.create_context(standalone=True)
        self.cache = resources.Cache(self.ctx)

        self.sys = particles.ParticleSystem(self.ctx, self.cache, 5000, 150)

    def test_emit(self):
        self.assertEqual(len(self.sys), 0)
        self.sys.emit(origin=pygame.math.Vector2(2, 3), radius=5.0, color=pygame.Color('red'),
                      impact=pygame.math.Vector2(0, 1), delta_degree=90)
        self.assertEqual(len(self.sys), 1)
        self.assertEqual(len(self.sys._data.tobytes()), 1 * len(particles.Offset) * 4)

        # can emit up to the maximum number of particles
        for _ in range(4999):
            self.sys.emit(origin=pygame.math.Vector2(2, 3), radius=5.0, color=pygame.Color('red'),
                          impact=pygame.math.Vector2(0, 1), delta_degree=90)
        self.assertEqual(len(self.sys), 5000)
        self.assertEqual(len(self.sys._data.tobytes()), 5000 * len(particles.Offset) * 4)
        self.sys.render(glm.mat4x4(), glm.mat4x4())

        # emit one more is skipped
        self.sys.emit(origin=pygame.math.Vector2(2, 3), radius=5.0, color=pygame.Color('red'),
                      impact=pygame.math.Vector2(0, 1), delta_degree=90)
        self.assertEqual(len(self.sys), 5000)
        self.assertEqual(len(self.sys._data.tobytes()), 5000 * len(particles.Offset) * 4)

    def test_position_update(self):
        for _ in range(2):
            self.sys.emit(origin=pygame.math.Vector2(2, 3), radius=5.0, color=pygame.Color('red'),
                          impact=pygame.math.Vector2(0, 1), delta_degree=90)

        x_offset = particles.Offset.POS_X
        y_offset = particles.Offset.POS_Y

        pos_x = self.sys._data[0, x_offset] + self.sys._data[0, particles.Offset.DIR_X] * 10 * particles.SPEED
        pos_y = self.sys._data[0, y_offset] + self.sys._data[0, particles.Offset.DIR_Y] * 10 * particles.SPEED

        pos_x2 = self.sys._data[1, x_offset] + self.sys._data[1, particles.Offset.DIR_X] * 10 * particles.SPEED
        pos_y2 = self.sys._data[1, y_offset] + self.sys._data[1, particles.Offset.DIR_Y] * 10 * particles.SPEED

        self.sys.update(10)
        self.assertAlmostEqual(self.sys._data[0, x_offset], pos_x, 2)
        self.assertAlmostEqual(self.sys._data[0, y_offset], pos_y, 2)
        self.assertAlmostEqual(self.sys._data[1, x_offset], pos_x2, 2)
        self.assertAlmostEqual(self.sys._data[1, y_offset], pos_y2, 2)

    def test_scale_update(self):
        for _ in range(2):
            self.sys.emit(origin=pygame.math.Vector2(2, 3), radius=5.0, color=pygame.Color('red'),
                          impact=pygame.math.Vector2(0, 1), delta_degree=90)

        scale = self.sys._data[0, particles.Offset.SCALE]

        self.sys.update(10)
        self.assertEqual(len(self.sys), 2)
        self.assertLess(self.sys._data[0, particles.Offset.SCALE], scale)

        # cleanup
        self.sys.update(10000)
        self.assertEqual(len(self.sys), 0)
