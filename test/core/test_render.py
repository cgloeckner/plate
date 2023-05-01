import unittest
import moderngl
import pygame

from core import render


class RenderTest(unittest.TestCase):

    def setUp(self):
        self.ctx = moderngl.create_context(standalone=True)
        self.tex = self.ctx.texture((10, 8), 4)

    def test_init(self):
        s = render.Sprite(self.tex)
        self.assertEqual(s.clip.x, 0)
        self.assertEqual(s.clip.y, 0)
        self.assertEqual(s.clip.w, 10)
        self.assertEqual(s.clip.h, 8)

        s = render.Sprite(self.tex, clip=pygame.Rect(1, 2, 3, 4))
        self.assertEqual(s.clip.x, 1)
        self.assertEqual(s.clip.y, 2)
        self.assertEqual(s.clip.w, 3)
        self.assertEqual(s.clip.h, 4)

    def test_tuple(self):
        s = render.Sprite(self.tex, pygame.Rect(6, 7, 8, 9))
        s.center.x = 1
        s.center.y = 2
        s.scale.x = 3
        s.scale.y = 4
        s.rotation = 5
        s.brightness = 10
        s.color = pygame.Color(255, 0, 255)

        t = s.as_tuple()
        self.assertEqual(len(t), len(render.Offset))
        self.assertEqual(t[render.Offset.POS_X], s.center.x)
        self.assertEqual(t[render.Offset.POS_Y], s.center.y)
        self.assertEqual(t[render.Offset.SIZE_X], s.clip.w * s.scale.x)
        self.assertEqual(t[render.Offset.SIZE_Y], s.clip.h * s.scale.y)
        self.assertEqual(t[render.Offset.ROTATION], s.rotation)
        self.assertEqual(t[render.Offset.COLOR_R], s.color.a / 255.0)
        self.assertEqual(t[render.Offset.COLOR_G], s.color.g / 255.0)
        self.assertEqual(t[render.Offset.COLOR_B], s.color.b / 255.0)
        self.assertEqual(t[render.Offset.COLOR_A], s.color.a / 255.0)
        self.assertEqual(t[render.Offset.CLIP_X], s.clip.x / 10)
        self.assertEqual(t[render.Offset.CLIP_Y], s.clip.y / 8)
        self.assertEqual(t[render.Offset.CLIP_W], s.clip.w / 10)
        self.assertEqual(t[render.Offset.CLIP_H], s.clip.h / 8)
        self.assertEqual(t[render.Offset.BRIGHTNESS], s.brightness)
