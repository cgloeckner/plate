import unittest
import moderngl
import pygame

from core import text


class TextTest(unittest.TestCase):

    def setUp(self) -> None:
        pygame.font.init()

        self.ctx = moderngl.create_context(standalone=True)
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 15)

    def tearDown(self) -> None:
        self.ctx.release()

        pygame.font.quit()

    def test_set_string(self):
        t = text.Text(self.ctx, self.font)
        self.assertIsNone(t.sprite)

        t.set_string('hello world')
        self.assertIsNotNone(t.sprite)
