import numpy
import pygame
import random

import core

from . import scene


BREAK: float = 0.0015


class ControlsSystem(scene.BaseSystem):
    def __init__(self, scene_obj: scene.Scene):
        super().__init__(scene_obj)

        self.forward = pygame.math.Vector2(0, 1)

    def accelerate(self, index: int, elapsed_ms: int) -> None:
        rot = self.scene.spacecrafts.data[index, core.SpriteOffset.ROTATION]

        vel = self.forward.rotate(rot)
        self.scene.spacecrafts.data[index, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y + 1] = vel.xy

        impact = self.forward.rotate(rot)
        pos = pygame.math.Vector2(
            *self.scene.spacecrafts.data[index, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y + 1]) - impact * 16
        self.scene.particles.emit(origin=pos, radius=4.0, color=pygame.Color('orange'), impact=impact,
                                  delta_degree=170)

    def decelerate(self, index: int, elapsed_ms: int) -> None:
        self.scene.spacecrafts.data[index, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y + 1] *= numpy.exp(
            -BREAK * elapsed_ms)

    def rotate(self, index: int, elapsed_ms: int) -> None:
        # NOTE: elapsed_ms is negative if rotating in the opposite direction
        delta = 0.075 * elapsed_ms

        vel_x, vel_y = self.scene.spacecrafts.data[index, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y + 1]
        vel = pygame.math.Vector2(vel_x, vel_y).rotate(delta)
        self.scene.spacecrafts.data[index, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y + 1] = vel.xy

        self.scene.spacecrafts.data[index, core.SpriteOffset.ROTATION] += delta

    def update_player(self, elapsed_ms: int) -> None:

        keys = pygame.key.get_pressed()

        # basic controls
        if keys[pygame.K_w]:
            self.accelerate(0, elapsed_ms)
        if keys[pygame.K_s]:
            self.decelerate(0, elapsed_ms)
        if keys[pygame.K_q]:
            self.rotate(0, elapsed_ms)
        if keys[pygame.K_e]:
            self.rotate(0, -elapsed_ms)

        # zoom
        if keys[pygame.K_PLUS]:
            self.scene.camera.zoom *= (1 + 0.001 * elapsed_ms)
            if self.scene.camera.zoom > 5.0:
                self.scene.camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            self.scene.camera.zoom *= (1 - 0.001 * elapsed_ms)
            if self.scene.camera.zoom < 0.25:
                self.scene.camera.zoom = 0.25

    def update_enemy(self, index: int, elapsed_ms: int) -> None:
        self.scene.spacecrafts.data[index, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y+1] = \
            self.scene.spacecrafts.data[0, core.SpriteOffset.VEL_X:core.SpriteOffset.VEL_Y+1]

        self.scene.spacecrafts.data[index, core.SpriteOffset.ROTATION] = \
            self.scene.spacecrafts.data[0, core.SpriteOffset.ROTATION]

        """
        player_pos = pygame.math.Vector2(
            *self.scene.spacecrafts.data[0, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y + 1])
        own_pos = pygame.math.Vector2(
            *self.scene.spacecrafts.data[index, core.SpriteOffset.POS_X:core.SpriteOffset.POS_Y + 1])
        direction = player_pos - own_pos

        if direction.length() > 10000.0:
            self.decelerate(index, elapsed_ms)
            return

        delta = self.forward.rotate(self.scene.spacecrafts.data[index, core.SpriteOffset.ROTATION]).angle_to(direction)

        if delta < 0:
            self.rotate(index, -elapsed_ms)
        if delta > 0:
            self.rotate(index, elapsed_ms)

        self.accelerate(index, elapsed_ms)
        """

    def update(self, elapsed_ms: int) -> None:
        self.update_player(elapsed_ms)

        for index in range(len(self.scene.spacecrafts)-1):
            self.update_enemy(index + 1, elapsed_ms)
