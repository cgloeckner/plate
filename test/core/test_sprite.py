import unittest
import moderngl
import pygame

from core import sprite


class SpriteTest(unittest.TestCase):

    def setUp(self) -> None:
        self.ctx = moderngl.create_context(standalone=True)
        self.tex = self.ctx.texture((10, 8), 4)

    def tearDown(self) -> None:
        self.ctx.release()

    def test_post_init(self):
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

    def test_to_array(self):
        s = sprite.Sprite(self.tex, clip=pygame.Rect(1, 2, 10, 8))
        s.center.x = 70
        s.center.y = 71
        s.velocity.x = 72
        s.velocity.y = 73
        s.origin.x = 0.75
        s.origin.y = 0.9
        s.rotation = 135
        s.color = pygame.Color(123, 63, 94)
        s.brightness = 1.32

        arr = s.to_array()
        self.assertAlmostEqual(arr[sprite.Offset.POS_X], 70)
        self.assertAlmostEqual(arr[sprite.Offset.POS_Y], 71)
        self.assertAlmostEqual(arr[sprite.Offset.VEL_X], 72)
        self.assertAlmostEqual(arr[sprite.Offset.VEL_Y], 73)
        self.assertAlmostEqual(arr[sprite.Offset.ORIGIN_X], 0.75)
        self.assertAlmostEqual(arr[sprite.Offset.ORIGIN_Y], 0.9)
        self.assertAlmostEqual(arr[sprite.Offset.SIZE_X], s.clip.w * s.scale)
        self.assertAlmostEqual(arr[sprite.Offset.SIZE_Y], s.clip.h * s.scale)
        self.assertAlmostEqual(arr[sprite.Offset.ROTATION], 135)
        self.assertAlmostEqual(arr[sprite.Offset.COLOR_R], 123/255.0)
        self.assertAlmostEqual(arr[sprite.Offset.COLOR_G], 63/255.0)
        self.assertAlmostEqual(arr[sprite.Offset.COLOR_B], 94/255.0)
        self.assertAlmostEqual(arr[sprite.Offset.COLOR_A], 1.0)
        self.assertAlmostEqual(arr[sprite.Offset.CLIP_X], s.clip.x / self.tex.size[0])
        self.assertAlmostEqual(arr[sprite.Offset.CLIP_Y], s.clip.y / self.tex.size[1])
        self.assertAlmostEqual(arr[sprite.Offset.CLIP_W], s.clip.w / self.tex.size[0])
        self.assertAlmostEqual(arr[sprite.Offset.CLIP_H], s.clip.h / self.tex.size[1])
        self.assertAlmostEqual(arr[sprite.Offset.BRIGHTNESS], 1.32, 5)

    def test_get_center(self):
        s = sprite.Sprite(self.tex, clip=pygame.Rect(1, 2, 10, 8))
        s.center.x = 70
        s.center.y = 71

        arr = s.to_array()
        pos = sprite.Sprite.get_center(arr)

        self.assertAlmostEqual(pos.x, s.center.x)
        self.assertAlmostEqual(pos.y, s.center.y)


# ----------------------------------------------------------------------------------------------------------------------

class SpriteArrayTest(unittest.TestCase):

    def setUp(self) -> None:
        self.ctx = moderngl.create_context(standalone=True)
        self.tex = self.ctx.texture((10, 8), 4)
        self.arr = sprite.SpriteArray()

    def tearDown(self) -> None:
        self.ctx.release()

    def test_add(self):
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
        self.arr.add(s)

        self.assertEqual(len(self.arr), 1)
        single_arr = s.to_array()
        for i in sprite.Offset:
            self.assertAlmostEqual(self.arr.data[0, i], single_arr[i])

    def test_clear(self):
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

        self.arr.add(s)
        self.assertEqual(len(self.arr), 1)
        self.arr.add(s)
        self.assertEqual(len(self.arr), 2)

        self.arr.clear()
        self.assertEqual(len(self.arr), 0)
