import unittest
import moderngl

from core import light


class LightTest(unittest.TestCase):

    def setUp(self) -> None:
        self.ctx = moderngl.create_context(standalone=True)

    def tearDown(self) -> None:
        self.ctx.release()

    def test_create_lightmap(self):
        # FIXME: cannot return to screen framebuffer because of headless mode
        # tex = light.create_lightmap(self.ctx, radius=5)
        # self.assertIsNotNone(tex)
        pass
