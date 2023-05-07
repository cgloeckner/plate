import moderngl
import pygame
import numpy

from dataclasses import dataclass, field
from enum import IntEnum, auto


@dataclass
class Sprite:
    texture: moderngl.Texture

    center: pygame.math.Vector2 = field(default_factory=pygame.math.Vector2)
    velocity: pygame.math.Vector2 = field(default_factory=pygame.math.Vector2)
    origin: pygame.math.Vector2 = field(default_factory=lambda: pygame.math.Vector2(0.5, 0.5))

    color: pygame.Color = field(default_factory=lambda: pygame.Color('white'))
    clip: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, -1, 0))

    scale: float = 1.0
    rotation: float = 0.0
    brightness: float = 1.0

    def __post_init__(self):
        self.color.a = 0
        if self.clip.w == -1:
            self.clip = pygame.Rect(0, 0, *self.texture.size)

    def to_array(self) -> numpy.ndarray:
        # prepare data
        size = pygame.math.Vector2(self.clip.size) * self.scale
        color_norm = self.color.normalize()
        tex_size = pygame.math.Vector2(self.texture.size)
        clip_xy = pygame.math.Vector2(self.clip.topleft).elementwise() / tex_size
        clip_wh = pygame.math.Vector2(self.clip.size).elementwise() / tex_size

        data = numpy.zeros((len(Offset)), dtype=numpy.float32)
        # create particle data
        data[Offset.POS_X] = self.center.x
        data[Offset.POS_Y] = self.center.y
        data[Offset.VEL_X] = self.velocity.x
        data[Offset.VEL_Y] = self.velocity.y
        data[Offset.ORIGIN_X] = self.origin.x
        data[Offset.ORIGIN_Y] = self.origin.y
        data[Offset.SIZE_X] = size.x
        data[Offset.SIZE_Y] = size.y
        data[Offset.ROTATION] = self.rotation
        data[Offset.COLOR_R] = color_norm[0]
        data[Offset.COLOR_G] = color_norm[1]
        data[Offset.COLOR_B] = color_norm[2]
        data[Offset.COLOR_A] = color_norm[3]
        data[Offset.CLIP_X] = clip_xy.x
        data[Offset.CLIP_Y] = clip_xy.y
        data[Offset.CLIP_W] = clip_wh.x
        data[Offset.CLIP_H] = clip_wh.y
        data[Offset.BRIGHTNESS] = self.brightness

        return data

    @staticmethod
    def from_array(data: numpy.ndarray, texture: moderngl.Texture) -> 'Sprite':
        s = Sprite(texture=texture)
        s.center.x = data[Offset.POS_X]
        s.center.y = data[Offset.POS_Y]
        s.velocity.x = data[Offset.VEL_X]
        s.velocity.y = data[Offset.VEL_Y]
        s.origin.x = data[Offset.ORIGIN_X]
        s.origin.y = data[Offset.ORIGIN_Y]
        s.rotation = data[Offset.ROTATION]
        s.color = pygame.Color([int(data[offset] * 255) for offset in [Offset.COLOR_R, Offset.COLOR_G, Offset.COLOR_B,
                                                                       Offset.COLOR_A]])
        s.brightness = data[Offset.BRIGHTNESS]
        s.clip.x = data[Offset.CLIP_X] * texture.size[0]
        s.clip.y = data[Offset.CLIP_Y] * texture.size[1]
        s.clip.w = data[Offset.CLIP_W] * texture.size[0]
        s.clip.h = data[Offset.CLIP_H] * texture.size[1]

        s.scale = data[Offset.SIZE_X] / s.clip.w
        return s


class Offset(IntEnum):
    """Provides offsets for accessing individual data within the RenderBatch's array."""
    POS_X = 0
    POS_Y = auto()
    VEL_X = auto()
    VEL_Y = auto()
    ORIGIN_X = auto()
    ORIGIN_Y = auto()
    SIZE_X = auto()
    SIZE_Y = auto()
    ROTATION = auto()
    COLOR_R = auto()
    COLOR_G = auto()
    COLOR_B = auto()
    COLOR_A = auto()
    CLIP_X = auto()
    CLIP_Y = auto()
    CLIP_W = auto()
    CLIP_H = auto()
    BRIGHTNESS = auto()


class SpriteArray:
    """Stores and manipulates sprite data in a tightly packed form."""

    def __init__(self):
        """Initializes the array."""
        self.data = numpy.zeros((0, len(Offset)), dtype=numpy.float32)

    def __len__(self) -> int:
        """Returns the number of sprite."""
        return self.data.shape[0]

    def add(self, sprite: Sprite) -> None:
        """Add the given sprite to the sprite array."""
        # resize array
        self.data.resize((self.data.shape[0] + 1, self.data.shape[1]), refcheck=False)
        index = self.data.shape[0] - 1

        # insert sprite data
        self.data[index] = sprite.to_array()

    def clear(self) -> None:
        """Clear the entire array."""
        self.data = numpy.zeros((0, len(Offset)), dtype=numpy.float32)
