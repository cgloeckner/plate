import unittest
import pygame
import moderngl

from core import resources, particles


class ParticlesTest(unittest.TestCase):

    def setUp(self):
        self.ctx = moderngl.create_context(standalone=True)
        self.cache = resources.Cache(self.ctx)

        self.sys = particles.ParticleSystem(self.ctx, self.cache, 2, 1500)
        self.assertEqual(len(self.sys), 0)
        self.sys.emit(2, impact=pygame.math.Vector2(0, 1), delta_degree=90, origin=pygame.math.Vector2(2, 3),
                      radius=5.0, speed=20.0, color=pygame.Color('red'))
        self.assertEqual(len(self.sys), 2)

    def test_position_update(self):
        pos_x = self.sys._data[particles.Offset.POS_X] + self.sys._data[particles.Offset.DIR_X] * 10 * particles.SPEED
        pos_y = self.sys._data[particles.Offset.POS_Y] + self.sys._data[particles.Offset.DIR_Y] * 10 * particles.SPEED

        pos_x2 = self.sys._data[len(particles.Offset) + particles.Offset.POS_X] + \
                 self.sys._data[len(particles.Offset) + particles.Offset.DIR_X] * 10 * particles.SPEED
        pos_y2 = self.sys._data[len(particles.Offset) + particles.Offset.POS_Y] + \
                 self.sys._data[len(particles.Offset) + particles.Offset.DIR_Y] * 10 * particles.SPEED

        self.sys.update(10)
        self.assertAlmostEqual(self.sys._data[particles.Offset.POS_X], pos_x, 3)
        self.assertAlmostEqual(self.sys._data[particles.Offset.POS_Y], pos_y, 3)
        self.assertAlmostEqual(self.sys._data[len(particles.Offset) + particles.Offset.POS_X], pos_x2, 3)
        self.assertAlmostEqual(self.sys._data[len(particles.Offset) + particles.Offset.POS_Y], pos_y2, 3)

    def test_scale_update(self):
        scale = self.sys._data[particles.Offset.SCALE]

        self.sys.update(10)
        self.assertEqual(len(self.sys), 2)
        self.assertLess(self.sys._data[particles.Offset.SCALE], scale)

        # cleanup
        self.sys.update(10000)
        self.assertEqual(len(self.sys), 0)
