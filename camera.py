import pygame
import glm


class Camera:
    def __init__(self):
        self.position = glm.vec3(0, 0, 1)
        self.rotation = 0.0

        self._up = glm.vec3(0, 1, 0)
        self._into = glm.vec3(0, 0, 1)

        self.m_view = self._get_view_matrix()
        self.m_proj = self._get_projection_matrix()

    def update(self) -> None:
        """Updates matrices after altering the camera or window size."""
        self.m_view = self._get_view_matrix()
        self.m_proj = self._get_projection_matrix()

    def _get_view_matrix(self) -> glm.mat4x4:
        """Return the view matrix (usually after camera moved)."""
        up_vector = glm.rotate(self._up, glm.radians(self.rotation), self._into)
        return glm.lookAt(self.position, self.position - self._into, up_vector)

    @staticmethod
    def _get_projection_matrix() -> glm.mat4x4:
        """Return the projection matrix (usually once)."""
        size = pygame.display.get_window_size()
        return glm.ortho(0, size[0], 0, size[1], 0.01, 50)
