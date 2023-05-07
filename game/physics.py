import numpy
import pygame

from typing import Callable
from enum import IntEnum, auto

import core
from game import scene


def update_movement(arr: core.SpriteArray, elapsed_ms: int, velocity_fade: float) -> None:
    """Update the sprites' positions using their velocity vectors."""
    # update positions
    arr.data[:, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y+1] += \
        arr.data[:, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y+1] * elapsed_ms

    # decrease velocity
    arr.data[:, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y+1] *= numpy.exp(-velocity_fade * elapsed_ms)


def query_collision_indices(first: numpy.ndarray, first_indices: numpy.ndarray, second: numpy.ndarray,
                            second_indices: numpy.ndarray, radius_mod: float) -> list:
    """Calculate all collisions between the given objects."""
    # extract relevant rows from the full arrays
    first_subset = first[first_indices, :]
    second_subset = second[second_indices, :]

    # calculate difference vectors between all points
    diff = (first_subset[:, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y + 1, numpy.newaxis] -
            second_subset[:, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y + 1, numpy.newaxis].T)
    dist_sq = numpy.sum(diff ** 2, axis=1)
    max_radii = (first_subset[:, core.SpriteOffset.SIZE_X, numpy.newaxis] * 0.5 * radius_mod +
                 second_subset[:, core.SpriteOffset.SIZE_X, numpy.newaxis].T * 0.5 * radius_mod) ** 2

    # calculate all collisions
    rows, cols = numpy.where(dist_sq <= max_radii)
    collisions = (rows, cols)

    # convert collisions' indices from subset to full array
    full_first_indices = first_indices[collisions[0]]
    full_second_indices = second_indices[collisions[1]]

    # create list of collision indices
    return [(full_first_indices[i], full_second_indices[i]) for i in range(len(collisions[0]))]


# ----------------------------------------------------------------------------------------------------------------------


class ObjectType(IntEnum):
    ASTEROID = 0
    SPACECRAFT = auto()


CollisionCallback = Callable[[int, ObjectType, int, ObjectType], None]


# ----------------------------------------------------------------------------------------------------------------------


class PhysicsSystem(scene.BaseSystem):

    def __init__(self, scene_obj: scene.Scene, callback: CollisionCallback):
        super().__init__(scene_obj)

        self._callback = callback

    def get_sprite_center(self, index: int, type_: ObjectType) -> pygame.math.Vector2:
        if type_ == ObjectType.ASTEROID:
            arr = self.scene.asteroids
        elif type_ == ObjectType.SPACECRAFT:
            arr = self.scene.spacecrafts
        else:
            raise NotImplemented

        return pygame.math.Vector2(*arr.data[index, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y+1])

    def on_collision(self, index1: int, type1: ObjectType, index2: int, type2: ObjectType) -> None:
        center1 = self.get_sprite_center(index1, type1)
        center2 = self.get_sprite_center(index2, type2)

        contact_point = (center1 + center2) / 2
        hex_color = '#422518' if type2 == ObjectType.ASTEROID else '#808080'
        self.scene.particles.emit(origin=contact_point, radius=2.0, color=pygame.Color(hex_color))

        self._callback(index1, type1, index2, type2)

    def update_pure_asteroids_collision(self) -> None:
        """Detects and handles collisions between asteroids."""
        data = self.scene.asteroids.data
        indices = self.scene.camera.query_visible(data)
        collision_indices = query_collision_indices(data, indices, data, indices, 1.0)
        for left, right in collision_indices:
            if left == right:
                continue
            self.on_collision(left, ObjectType.ASTEROID, right, ObjectType.ASTEROID)

    def update_pure_spacecraft_collision(self) -> None:
        """Detects and handles collisions between spacecrafts."""
        data = self.scene.spacecrafts.data
        indices = self.scene.camera.query_visible(data)
        collision_indices = query_collision_indices(data, indices, data, indices, 1.0)
        for left, right in collision_indices:
            if left == right:
                continue
            self.on_collision(left, ObjectType.SPACECRAFT, right, ObjectType.SPACECRAFT)

    def update_mixed_collision(self) -> None:
        """Detects and handles collisions between asteroids and spacecrafts."""
        asteroid_data = self.scene.asteroids.data
        asteroid_indices = self.scene.camera.query_visible(asteroid_data)
        spacecraft_data = self.scene.spacecrafts.data
        spacecraft_indices = self.scene.camera.query_visible(spacecraft_data)
        collision_indices = query_collision_indices(asteroid_data, asteroid_indices, spacecraft_data,
                                                    spacecraft_indices, 1.0)
        for asteroid_index, fighter_index in collision_indices:
            self.on_collision(asteroid_index, ObjectType.ASTEROID, fighter_index, ObjectType.SPACECRAFT)

    # FIXME:
    """
    def hit_asteroid(self, index: int) -> None:
        #Either shrink the asteroid or remove it completely.
        if self.sprites.data[index, sprite.Offset.SIZE_X] > 4.0:
            # shrink
            self.sprites.data[index, sprite.Offset.SIZE_X] *= 0.9
            self.sprites.data[index, sprite.Offset.SIZE_Y] *= 0.9

            # reverse velocity vector
            self.sprites.data[index, sprite.Offset.VEL_X] *= -1
            self.sprites.data[index, sprite.Offset.VEL_Y] *= -1
            return

        self.sprites.data = numpy.delete(self.sprites.data, index, axis=0)
    """

    def update(self, elapsed_ms) -> None:
        # update spacecrafts
        update_movement(self.scene.spacecrafts, elapsed_ms, velocity_fade=0.0005)

        # use asteroids (pos, rotate
        update_movement(self.scene.asteroids, elapsed_ms, velocity_fade=0.0)
        self.scene.asteroids.data[:, core.SpriteOffset.ROTATION] += elapsed_ms * 0.01

        # sort asteroids by SIZE_X (descending)
        indices = numpy.argsort(-self.scene.asteroids.data[:, core.SpriteOffset.SIZE_X])
        self.scene.asteroids.data = self.scene.asteroids.data[indices]

        # handle collision stuff
        self.update_pure_asteroids_collision()
        self.update_pure_spacecraft_collision()
        self.update_mixed_collision()
