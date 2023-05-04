import unittest
import moderngl
import pygame

from core import sprite


class RenderTest(unittest.TestCase):

    def setUp(self):
        self.ctx = moderngl.create_context(standalone=True)
        self.tex = self.ctx.texture((10, 8), 4)

    def test_init(self):
        s = sprite.Sprite(self.tex)
        self.assertEqual(s.clip.x, 0)
        self.assertEqual(s.clip.y, 0)
        self.assertEqual(s.clip.w, 10)
        self.assertEqual(s.clip.h, 8)

        s = sprite.Sprite(self.tex, clip=pygame.Rect(1, 2, 3, 4))
        self.assertEqual(s.clip.x, 1)
        self.assertEqual(s.clip.y, 2)
        self.assertEqual(s.clip.w, 3)
        self.assertEqual(s.clip.h, 4)

    def test_add(self):
        arr = sprite.SpriteArray()
        s = sprite.Sprite(self.tex)
        s.center.x = 70
        s.center.y = 71
        s.velocity.x = 72
        s.velocity.y = 73
        s.origin.x = 0.75
        s.origin.y = 0.9
        s.rotation = 135
        s.color = pygame.Color(123, 63, 94)
        s.brightness = 1.32
        arr.add(s)

        self.assertEqual(len(arr), 1)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.POS_X], s.center.x)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.POS_Y], s.center.y)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.VEL_X], s.velocity.x)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.VEL_Y], s.velocity.y)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.ORIGIN_X], s.origin.x)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.ORIGIN_Y], s.origin.y)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.SIZE_X], s.clip.w * s.scale.x)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.SIZE_Y], s.clip.h * s.scale.y)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.ROTATION], s.rotation)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.COLOR_R], s.color.r / 255.0)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.COLOR_G], s.color.g / 255.0)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.COLOR_B], s.color.b / 255.0)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.CLIP_X], s.clip.x / 10)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.CLIP_Y], s.clip.y / 8)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.CLIP_W], s.clip.w / 10)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.CLIP_H], s.clip.h / 8)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.BRIGHTNESS], s.brightness, 5)

    def test_update_movement(self):
        arr = sprite.SpriteArray()
        s1 = sprite.Sprite(self.tex)
        s1.velocity.x = 1.0
        s2 = sprite.Sprite(self.tex)
        s3 = sprite.Sprite(self.tex)
        s3.velocity.x = 0.7
        s3.velocity.y = -1.0
        arr.add(s1)
        arr.add(s2)
        arr.add(s3)

        sprite.update_movement(arr, 10)

        # expect changed positions
        self.assertEqual(arr.data[0, sprite.Offset.POS_X], s1.center.x + s1.velocity.x * 10)
        self.assertEqual(arr.data[0, sprite.Offset.POS_Y], s1.center.y)
        self.assertEqual(arr.data[1, sprite.Offset.POS_X], s2.center.x)
        self.assertEqual(arr.data[1, sprite.Offset.POS_Y], s2.center.y)
        self.assertEqual(arr.data[2, sprite.Offset.POS_X], s3.center.x + s3.velocity.x * 10)
        self.assertEqual(arr.data[2, sprite.Offset.POS_Y], s3.center.y + s3.velocity.y * 10)

        # expect decreased velocities
        self.assertLess(arr.data[0, sprite.Offset.VEL_X], s1.velocity.x)
        self.assertAlmostEqual(arr.data[0, sprite.Offset.VEL_Y], s1.velocity.y)
        self.assertAlmostEqual(arr.data[1, sprite.Offset.VEL_X], s2.velocity.x)
        self.assertAlmostEqual(arr.data[1, sprite.Offset.VEL_Y], s2.velocity.y)
        self.assertLess(abs(arr.data[2, sprite.Offset.VEL_X]), abs(s3.velocity.x))
        self.assertLess(abs(arr.data[2, sprite.Offset.VEL_Y]), abs(s3.velocity.y))
