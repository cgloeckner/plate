import pygame
import glm


class Camera:
    def __init__(self, window: pygame.Surface):
        self.position = glm.vec3(0, 0, 1)
        self.rotation = 0.0

        self._window_size = window.get_size()
        self._aspect_ratio = self._window_size[0] / self._window_size[1]

        self._right = glm.vec3(1, 0, 0)
        self._up = glm.vec3(0, 1, 0)
        self._into = glm.vec3(0, 0, 1)

        self.m_view = self._get_view_matrix()
        self.m_proj = self._get_projection_matrix()

    def update(self) -> None:
        """Updates matrices after altering the camera."""
        self.m_view = self._get_view_matrix()
        self.m_proj = self._get_projection_matrix()

    def _get_view_matrix(self) -> glm.mat4x4:
        """Return the view matrix (usually after camera moved)."""
        up_vector = glm.rotate(self._up, glm.radians(self.rotation), glm.vec3(0.0, 0.0, 1.0))
        return glm.lookAt(self.position, self.position - self._into, up_vector)

    def _get_projection_matrix(self) -> glm.mat4x4:
        """Return the projection matrix (usually once)."""
        return glm.ortho(-self._aspect_ratio * self.position.z, self._aspect_ratio * self.position.z,
                         -self.position.z, self.position.z, 0.01, 50)

