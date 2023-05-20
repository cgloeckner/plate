import unittest
import pygame
import moderngl
import tempfile
import pathlib

from core import resources


class ResourcesTest(unittest.TestCase):

    def setUp(self):
        self.ctx = moderngl.create_context(standalone=True)
        self.cache = resources.Cache(self.ctx)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp_dir.name)

        self.svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="210mm"
   height="297mm"
   viewBox="0 0 210 297"
   version="1.1"
   id="svg8"
   inkscape:version="0.92.5 (2060ec1f9f, 2020-04-08)"
   sodipodi:docname="minimal.svg">
  <defs
     id="defs2" />
  <sodipodi:namedview
     id="base"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageopacity="0.0"
     inkscape:pageshadow="2"
     inkscape:zoom="0.35"
     inkscape:cx="-400"
     inkscape:cy="560"
     inkscape:document-units="mm"
     inkscape:current-layer="layer1"
     showgrid="false"
     inkscape:window-width="1680"
     inkscape:window-height="943"
     inkscape:window-x="0"
     inkscape:window-y="29"
     inkscape:window-maximized="1" />
  <metadata
     id="metadata5">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     inkscape:label="Ebene 1"
     inkscape:groupmode="layer"
     id="layer1">
    <rect
       style="opacity:1;fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:#000000;stroke-width:0.91099995;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:75.59055328;stroke-opacity:1;paint-order:markers fill stroke"
       id="rect815"
       width="11.339286"
       height="9.0714283"
       x="49.136902"
       y="58.875" />
  </g>
</svg>
'''
        self.shader_content = 'void main() {}'

    def tearDown(self) -> None:
        self.ctx.release()

    def test_texture_from_surface(self):
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surf, pygame.Color('red'), (10, 10), 8)

        tex = resources.texture_from_surface(self.ctx, surf)
        # FIXME: more detailed testing?
        self.assertIsNotNone(tex)

    def test_get_png(self):
        file_name = str(self.root / 'image.png')

        # cannot load non-existing image
        with self.assertRaises(FileNotFoundError):
            tex = self.cache.get_png(file_name)

        # create demo image
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surf, pygame.Color('red'), (10, 10), 8)
        pygame.image.save(surf, file_name)

        # can load image from file
        tex = self.cache.get_png(file_name)
        # FIXME: more detailed testing?
        self.assertIsNotNone(tex)

        # place dummy-texture in cache
        dummy = self.ctx.texture(size=(20, 20), components=4)
        self.cache.png_cache[file_name] = dummy

        # can load image from cache
        tex = self.cache.get_png(file_name)
        self.assertEqual(tex, dummy)

    def test_get_svg(self):
        file_name = str(self.root / 'image.svg')

        # cannot load non-existing image
        with self.assertRaises(FileNotFoundError):
            tex = self.cache.get_png(file_name)

        # create demo svg
        with open(file_name, 'w') as file:
            file.write(self.svg_content)

        # can load image from file
        tex = self.cache.get_svg(file_name, scale=2.5)
        # FIXME: more detailed testing?
        self.assertIsNotNone(tex)

        # place dummy-texture in cache
        dummy = self.ctx.texture(size=(20, 20), components=4)
        self.cache.svg_cache[(file_name, 2.5)] = dummy

        # can load image from cache
        tex = self.cache.get_svg(file_name, scale=2.5)
        self.assertEqual(tex, dummy)

    def test_get_shader(self):
        file_name = str(self.root / 'shader.c')

        # cannot load non-existing shader
        with self.assertRaises(FileNotFoundError):
            shader = self.cache.get_shader(file_name)

        # create demo shader
        with open(file_name, 'w') as file:
            file.write(self.shader_content)

        # can load image from file
        shader = self.cache.get_shader(file_name)
        # FIXME: more detailed testing?
        self.assertEqual(shader, self.shader_content)

        # place dummy-shader in cache
        dummy = '// nothing'
        self.cache.shader_cache[file_name] = dummy

        # can load image from cache
        shader = self.cache.get_shader(file_name)
        self.assertEqual(shader, dummy)

    def test_get_shaders(self):
        file_name = str(self.root / 'shader')
        types = ['vert', 'geom', 'frag']

        # cannot load non-existing shader
        with self.assertRaises(FileNotFoundError):
            shaders = self.cache.get_shaders(file_name, types)

        # create demo shaders
        for type_ in types:
            with open(f'{file_name}.{type_}', 'w') as file:
                file.write(f'// {type_}\n')
                file.write(self.shader_content)

        # can load shaders from files
        shaders = self.cache.get_shaders(file_name, types)
        self.assertTrue(shaders[0].startswith('// vert\n'))
        self.assertTrue(shaders[1].startswith('// geom\n'))
        self.assertTrue(shaders[2].startswith('// frag\n'))

        # place dummy-shaders in cache
        dummy = '// nothing'
        self.cache.shader_cache[f'{file_name}.vert'] = dummy
        self.cache.shader_cache[f'{file_name}.geom'] = dummy
        self.cache.shader_cache[f'{file_name}.frag'] = dummy

        # can load shaders from cache
        shaders = self.cache.get_shaders(file_name, types)
        self.assertEqual(shaders[0], dummy)
        self.assertEqual(shaders[1], dummy)
        self.assertEqual(shaders[2], dummy)

    def test_get_font(self):
        # FIXME: not fully implemented yet
        pass
