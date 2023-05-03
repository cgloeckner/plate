import moderngl
import pygame
import numpy

from typing import Optional
from enum import IntEnum, auto


SPEED: float = 0.01


class Sprite:
    """Combines sprite data such as

    position: as pygame.math.Vector2, defaults to (0, 0)
    origin: as pygame.math.Vector2, defaults to (0.5, 0.5)
    scale: as pygame.math.Vector2, defaults to either the clipping size (if provided) or the texture size (fallback)
    rotation: as float in degree, defaults to 0
    color: as pygame.Color, defaults to 'white', but with alpha=0 of 255 (which gives 0% shift)
    texture: as provided
    clip: as pygame.Rect in pixel coordinates
    brightness: as float, defaults to 1.0
    """

    def __init__(self, texture: moderngl.Texture, clip: Optional[pygame.Rect] = None):
        """Creates a sprite using a texture and an optional clipping rectangle."""
        self.center = pygame.math.Vector2(0, 0)
        self.origin = pygame.math.Vector2(0.5, 0.5)
        self.scale = pygame.math.Vector2(1, 1)
        self.rotation = 0.0
        self.color = pygame.Color('white')
        self.color.a = 0
        self.brightness = 1.0
        self.clip = pygame.Rect(0, 0, *texture.size) if clip is None else clip
        self.texture = texture
        self.velocity = pygame.math.Vector2(0, 0)

    def to_array(self) -> numpy.ndarray:
        # prepare data
        size = pygame.math.Vector2(self.clip.size).elementwise() * self.scale
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

    def add(self, sprite: Sprite) -> None:
        """Add the given sprite to the sprite array."""
        # resize array
        self.data.resize((self.data.shape[0] + 1, self.data.shape[1]), refcheck=False)
        index = self.data.shape[0] - 1

        # insert sprite data
        self.data[index] = sprite.to_array()

    def clear(self) -> None:
        self.data = numpy.zeros((0, len(Offset)), dtype=numpy.float32)

    def to_bytes(self) -> bytes:
        return self.data.tobytes()

    def update(self, elapsed_ms: int) -> None:
        # update positions
        displacement = self.data[:, Offset.VEL_X:Offset.VEL_Y] * elapsed_ms * SPEED
        self.data[:, Offset.POS_X:Offset.POS_Y] += displacement
