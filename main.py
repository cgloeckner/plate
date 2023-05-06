import pygame
import pygame.gfxdraw
import moderngl
import random
import numpy

from core import app, resources, particles, render, sprite, text


class StarField:
    def __init__(self, context: moderngl.Context, width: int, height: int, num_stars: int):
        surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        for _ in range(num_stars):
            x = random.randrange(width)
            y = random.randrange(height)
            v = random.randrange(255)
            color = pygame.Color(v, v, v, 255)
            pygame.draw.circle(surface, color, (x, y), 2.0)

        self.texture = resources.texture_from_surface(context, surface)
        self.texture.filter = moderngl.NEAREST, moderngl.NEAREST

        self.sprite = sprite.Sprite(texture=self.texture, origin=pygame.Vector2())


class AsteroidsField(render.RenderBatch):
    def __init__(self, context: moderngl.Context, cache: resources.Cache, field_size: int):
        self.sprites = sprite.SpriteArray()
        super().__init__(context, cache, field_size, self.sprites)

        self.tex = cache.get_svg('data/sprites/asteroid.svg', scale=10)
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST

    def __len(self) -> int:
        return self.get_data().shape[0]

    def get_data(self) -> numpy.ndarray:
        return self.sprites.data

    def add_asteroid(self, center: pygame.math.Vector2, scale: float, velocity: pygame.math.Vector2) -> None:
        s = sprite.Sprite(self.tex)
        s.center = center
        s.rotation = random.uniform(0.0, 360.0)
        s.scale *= scale / 10
        s.velocity = velocity
        self.add(s)

    def hit_asteroid(self, index: int) -> None:
        """Either shrink the asteroid or remove it completly."""
        if self.sprites.data[index, sprite.Offset.SIZE_X] > 4.0:
            # shrink
            self.sprites.data[index, sprite.Offset.SIZE_X] *= 0.9
            self.sprites.data[index, sprite.Offset.SIZE_Y] *= 0.9

            # reverse velocity vector
            self.sprites.data[index, sprite.Offset.VEL_X] *= -1
            self.sprites.data[index, sprite.Offset.VEL_Y] *= -1
            return

        self.sprites.data = numpy.delete(self.sprites.data, index, axis=0)

    def update(self, elapsed_ms: int) -> None:
        sprite.update_movement(self.sprites, elapsed_ms, velocity_fade=0.0)

        # update rotation
        self.sprites.data[:, sprite.Offset.ROTATION] += elapsed_ms * 0.01

        # sort by SIZE_X (descending)
        indices = numpy.argsort(-self.sprites.data[:, sprite.Offset.SIZE_X])
        self.sprites.data = self.sprites.data[indices]


def query_collision_indices(first: numpy.ndarray, first_indices: numpy.ndarray, second: numpy.ndarray,
                            second_indices: numpy.ndarray, radius_mod: float) -> list:
    """Calculate all collisions between the given objects."""
    # extract relevant rows from the full arrays
    first_subset = first[first_indices, :]
    second_subset = second[second_indices, :]

    # calculate difference vectors between all points
    diff = (first_subset[:, sprite.Offset.POS_X:sprite.Offset.POS_Y + 1, numpy.newaxis] -
            second_subset[:, sprite.Offset.POS_X:sprite.Offset.POS_Y + 1, numpy.newaxis].T)
    dist_sq = numpy.sum(diff ** 2, axis=1)
    max_radii = (first_subset[:, sprite.Offset.SIZE_X, numpy.newaxis] * 0.5 * radius_mod +
                 second_subset[:, sprite.Offset.SIZE_X, numpy.newaxis].T * 0.5 * radius_mod) ** 2

    # calculate all collisions
    rows, cols = numpy.where(dist_sq <= max_radii)
    collisions = (rows, cols)

    # convert collisions' indices from subset to full array
    full_first_indices = first_indices[collisions[0]]
    full_second_indices = second_indices[collisions[1]]

    #upper_indices = numpy.triu_indices(dist_sq.shape[0], k=1)
    #collisions = numpy.where(dist_sq[upper_indices] <= max_radii[upper_indices])
    #rows, cols = upper_indices

    # convert collisions' indices from subset to full array
    #full_first_indices = first_indices[rows[collisions]]
    #full_second_indices = second_indices[cols[collisions]]

    # create list of collision indices
    return [(full_first_indices[i], full_second_indices[i]) for i in range(len(collisions[0]))]


BREAK: float = 0.0015


class FighterSystem(render.RenderBatch):
    def __init__(self, context: moderngl.Context, cache: resources.Cache, particle_system: particles.ParticleSystem,
                 num_max_fighters: int):
        self.sprites = sprite.SpriteArray()
        super().__init__(context, cache, num_max_fighters, self.sprites)

        self.particle_system = particle_system

        self.tex = cache.get_png('data/sprites/ship.png')
        self.tex.filter = moderngl.NEAREST, moderngl.NEAREST

        self.forward = pygame.math.Vector2(0, 1)

    def __len__(self) -> int:
        return self.get_data().shape[0]

    def get_data(self) -> numpy.ndarray:
        return self.sprites.data

    def accelerate(self, index: int, elapsed_ms: int) -> None:
        rot = self.sprites.data[index, sprite.Offset.ROTATION]

        vel = self.forward.rotate(rot)
        self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1] = vel.xy

        impact = self.forward.rotate(rot)
        pos = pygame.math.Vector2(*self.sprites.data[index, sprite.Offset.POS_X:sprite.Offset.POS_Y+1]) - impact * 16
        if random.random() > 0.75:
            self.particle_system.emit(origin=pos, radius=4.0, color=pygame.Color('orange'), impact=impact,
                                      delta_degree=170)

    def decelerate(self, index: int, elapsed_ms: int) -> None:
        self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1] *= numpy.exp(-BREAK * elapsed_ms)

    def rotate(self, index: int, elapsed_ms: int) -> None:
        # NOTE: elapsed_ms is negative if rotating in the opposite direction
        delta = 0.075 * elapsed_ms

        vel_x, vel_y = self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1]
        vel = pygame.math.Vector2(vel_x, vel_y).rotate(delta)
        self.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1] = vel.xy

        self.sprites.data[index, sprite.Offset.ROTATION] += delta

    def update(self, elapsed_ms: int) -> None:
        sprite.update_movement(self.sprites, elapsed_ms)

    def update_enemy(self, index: int, elapsed_ms: int, total_ms: int) -> None:
        player_pos = pygame.math.Vector2(*self.sprites.data[0, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
        own_pos = pygame.math.Vector2(*self.sprites.data[index, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
        direction = player_pos - own_pos

        if direction.length() > 10000.0:
            self.decelerate(index, elapsed_ms)
            return

        delta = self.forward.rotate(self.sprites.data[index, sprite.Offset.ROTATION]).angle_to(direction)

        if delta < 0:
            self.rotate(index, -elapsed_ms)
        if delta > 0:
            self.rotate(index, elapsed_ms)

        if total_ms < 100:
            self.accelerate(index, elapsed_ms)


class DemoState(app.State):
    def __init__(self, engine: app.Engine):
        super().__init__(engine)
        self.cache = resources.Cache(engine.context)
        self.camera = render.Camera(engine.context, self.cache)
        self.gui = render.GuiCamera(engine.context, self.cache)
        self.parts = particles.ParticleSystem(self.engine.context, self.cache, 50000, 128)

        # create starfield background
        w, h = pygame.display.get_window_size()
        self.starfield = StarField(self.engine.context, w, h, int(min(w, h) ** 0.5))
        self.starfield.sprite.clip.w *= 10
        self.starfield.sprite.clip.h *= 10

        # create asteroids field
        self.asteroids = AsteroidsField(self.engine.context, self.cache, 10000)
        for _ in range(1000):
            x = random.randrange(0, 1600 * 10)
            y = random.randrange(0, 900 * 10)
            scale = random.uniform(0.5, 4.0)
            direction = pygame.math.Vector2(0, 1).rotate(random.uniform(0.0, 360.0)) * random.uniform(0.5, 4.0)
            direction *= 0.05
            self.asteroids.add_asteroid(pygame.math.Vector2(x, y), scale, direction)

        self.total_ms = 0
        self.fps = text.Text(self.engine.context, self.cache.get_font(font_size=30))

        # create fighters
        self.fighters = FighterSystem(self.engine.context, self.cache, self.parts, 1000)
        s = sprite.Sprite(self.fighters.tex, clip=pygame.Rect(0, 0, 32, 32))
        s.center.x = 8000
        s.center.y = 4500
        self.fighters.add(s)

        for i in range(100):
            s = sprite.Sprite(self.fighters.tex, clip=pygame.Rect(0, 0, 32, 32))
            s.center.x -= 200 + i * 50
            s.center.y -= 200 + i * 50
            s.color = pygame.Color('red')
            s.color.a = 96
            self.fighters.add(s)

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.engine.pop()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            enable = not self.asteroids.has_enabled_bounding_circles()
            self.asteroids.enable_bounding_circles(enable)
            self.fighters.enable_bounding_circles(enable)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.camera.to_world_pos(pygame.math.Vector2(pygame.mouse.get_pos()))
            indices = self.camera.query_visible(self.asteroids.sprites.data)

            # not used atm
            #exp = 0.1
            #if not pygame.mouse.get_pressed()[0]:
            #    exp *= -1

            # query at which asteroids the user clicked
            clicked = list()
            for i in indices:
                x, y = self.asteroids.sprites.data[i, sprite.Offset.POS_X:sprite.Offset.POS_Y+1]
                p = pygame.math.Vector2(x, y)
                r = self.asteroids.sprites.data[i, sprite.Offset.SIZE_X] // 2
                if p.distance_squared_to(pos) <= r ** 2:
                    # click on asteroid!
                    clicked.append(i)

            # traverse backwards to avoid index invalidation
            for index in reversed(clicked):
                x, y = self.asteroids.sprites.data[index, sprite.Offset.POS_X:sprite.Offset.POS_Y+1]
                dx, dy = self.asteroids.sprites.data[index, sprite.Offset.VEL_X:sprite.Offset.VEL_Y+1]
                size = max(self.asteroids.sprites.data[index, sprite.Offset.SIZE_X:sprite.Offset.SIZE_Y+1])
                for _ in range(100):
                    self.parts.emit(origin=pygame.math.Vector2(x, y),
                                    radius=size,
                                    color=pygame.Color('blue'),
                                    impact=pygame.math.Vector2(dx, dy))
                self.asteroids.hit_asteroid(index)
                # not used atm
                # self.asteroids.sprites.data[i, sprite.Offset.SIZE_X] *= numpy.exp(exp)
                # self.asteroids.sprites.data[i, sprite.Offset.SIZE_Y] *= numpy.exp(exp)

    def update_player(self, elapsed_ms: int) -> None:
        keys = pygame.key.get_pressed()

        # basic controls
        if keys[pygame.K_w]:
            self.fighters.accelerate(0, elapsed_ms)
        if keys[pygame.K_s]:
            self.fighters.decelerate(0, elapsed_ms)
        if keys[pygame.K_q]:
            self.fighters.rotate(0, elapsed_ms)
        if keys[pygame.K_e]:
            self.fighters.rotate(0, -elapsed_ms)

        # zoom
        if keys[pygame.K_PLUS]:
            self.camera.zoom *= (1 + 0.001 * elapsed_ms)
            if self.camera.zoom > 5.0:
                self.camera.zoom = 5.0
        if keys[pygame.K_MINUS]:
            self.camera.zoom *= (1 - 0.001 * elapsed_ms)
            if self.camera.zoom < 0.25:
                self.camera.zoom = 0.25

    def asteroids_collision_update(self) -> None:
        data = self.asteroids.get_data()
        indices = self.camera.query_visible(data)
        collision_indices = query_collision_indices(data, indices, data, indices, 1.0)
        for left, right in collision_indices:
            if left == right:
                continue
            left_sprite = sprite.Sprite.from_array(data[left], self.asteroids.tex)
            right_sprite = sprite.Sprite.from_array(data[right], self.asteroids.tex)
            contact_point = (left_sprite.center + right_sprite.center) / 2
            self.parts.emit(origin=contact_point,
                            radius=2.0,
                            color=pygame.Color('#422518'))
            #self.asteroids.hit_asteroid(left)
            #self.asteroids.hit_asteroid(right)

    def fighters_collision_update(self) -> None:
        data = self.fighters.get_data()
        indices = self.camera.query_visible(data)
        collision_indices = query_collision_indices(data, indices, data, indices, 1.0)
        for left, right in collision_indices:
            if left == right:
                continue
            left_sprite = sprite.Sprite.from_array(data[left], self.fighters.tex)
            right_sprite = sprite.Sprite.from_array(data[right], self.fighters.tex)
            contact_point = (left_sprite.center + right_sprite.center) / 2
            self.parts.emit(origin=contact_point,
                            radius=2.0,
                            color=pygame.Color('#808080'))

    def asteroids_fighters_collision_update(self) -> None:
        asteroid_data = self.asteroids.get_data()
        asteroid_indices = self.camera.query_visible(asteroid_data)
        fighter_data = self.fighters.get_data()
        fighter_indices = self.camera.query_visible(fighter_data)
        collision_indices = query_collision_indices(asteroid_data, asteroid_indices, fighter_data, fighter_indices, 1.0)
        for asteroid_index, fighter_index in collision_indices:
            asteroid_sprite = sprite.Sprite.from_array(asteroid_data[asteroid_index], self.asteroids.tex)
            fighter_sprite = sprite.Sprite.from_array(fighter_data[fighter_index], self.asteroids.tex)
            contact_point = (asteroid_sprite.center + fighter_sprite.center) / 2
            self.parts.emit(origin=contact_point,
                            radius=2.0,
                            color=pygame.Color('#808080'))

        """
        collision_indices = {val for tup in collision_indices for val in tup}
        collision_indices = sorted(list(collision_indices), reverse=True)
        for index in collision_indices:
            self.fighters.sprites.data = numpy.delete(self.fighters.sprites.data, index, axis=0)
        """

    def update(self, elapsed_ms) -> None:
        self.total_ms += elapsed_ms

        self.update_player(elapsed_ms)
        for index in range(len(self.fighters) - 1):
            self.fighters.update_enemy(index + 1, elapsed_ms, self.total_ms)

        self.asteroids.update(elapsed_ms)
        self.fighters.update(elapsed_ms)

        self.asteroids_collision_update()
        self.fighters_collision_update()
        self.asteroids_fighters_collision_update()

        # let camera follow player
        self.camera.center = pygame.math.Vector2(
            *self.fighters.sprites.data[0, sprite.Offset.POS_X:sprite.Offset.POS_Y+1])
        self.camera.rotation = self.fighters.sprites.data[0, sprite.Offset.ROTATION]

        self.camera.update()
        self.parts.update(elapsed_ms)

        num_fps = int(self.engine.clock.get_fps())
        if self.total_ms > 250:
            self.fps.set_string(f'FPS: {num_fps}\n{len(self.parts)} Particles\n{len(self.asteroids.get_data())} Asteroids'
                                f'\n{len(self.fighters.get_data())} Spaceships')
            self.total_ms -= 250

    def render(self) -> None:
        self.camera.render(self.starfield.sprite)
        self.camera.render_batch(self.asteroids)
        self.camera.render_particles(self.parts)
        self.camera.render_batch(self.fighters)

        self.gui.render_text(self.fps)


def main() -> None:
    engine = app.Engine(1600, 900)
    engine.push(DemoState(engine))
    engine.run()


if __name__ == '__main__':
    main()
