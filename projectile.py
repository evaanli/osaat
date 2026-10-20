import math

import pygame


# potion projectiles
class Potion:
    # speed
    SPEED = 300.0
    # potion draw radius
    RADIUS = 10
    # colour
    COLOR = (170, 75, 255)

    # harming potion
    def __init__(
        self,
        original=(0, 0),
        target=(10, 10),
        potion_type="harming",
        owner=None,
    ):
        # potion type
        self.type = potion_type
        # player number controlling this live recording projectile
        self.owner = owner
        # original position vector
        self.original = pygame.Vector2(original)
        # target position vector
        self.target = pygame.Vector2(target)
        # current position
        self.position = self.original.copy()

        # time elapsed
        self.elapsed = 0.0

        # current distance to target
        self.distance = self.original.distance_to(self.target)
        # travel time calculation
        self.travel_time = self.get_travel_time(
            self.original,
            self.target,
        )
        # arc height calculation
        self.arc_height = max(40.0, min(160.0, self.distance * 0.3))
        # status
        self.alive = True
        self.broken = False

        # if already at target then just break the potion
        if self.travel_time == 0.0:
            self.break_potion()

    # get travel tiem required from original to target
    @classmethod
    def get_travel_time(cls, original, target):
        # hypotenuse
        distance = math.hypot(
            target[0] - original[0],
            target[1] - original[1],
        )
        # return the time
        return distance / cls.SPEED

    # set elapsed time
    def set_elapsed(self, elapsed):
        # set elapsed time to above zero
        self.elapsed = max(0.0, elapsed)

        # if there is no time left or the elapsed time is over travle time then break the potion
        if self.travel_time == 0.0 or self.elapsed >= self.travel_time:
            self.break_potion()
            return

        # get progress percentage
        progress = self.elapsed / self.travel_time
        # get the position from the ground
        ground_position = self.original.lerp(self.target, progress)
        # get the height off the ground
        height = 4.0 * self.arc_height * progress * (1.0 - progress)
        # update the position
        self.position.update(ground_position.x, ground_position.y - height)
        # update status
        self.broken = False
        self.alive = True

    # when potion hits the groudn
    def break_potion(self):
        # position is the same as the target (perfect accuracy)
        self.position = self.target.copy()
        # update status
        self.broken = True
        self.alive = False

    # update the potion position and elapsed time
    def update(self, dt):
        self.set_elapsed(self.elapsed + max(0.0, dt))

    # draw the potion
    def draw(self, surface):
        if self.alive: # if alive
            pygame.draw.circle(
                surface,
                self.COLOR,
                (round(self.position.x), round(self.position.y)),
                self.RADIUS,
            )


# potion damage area
class PotionArea:
    # distance from the center that counts as touching
    RADIUS = 75
    # maximum amount of time the area can stay active
    DURATION = 2.0
    # damage dealt each time the cooldown allows a hit
    DAMAGE = 5
    # time before a player can take area damage again
    DAMAGE_INTERVAL = 0.75
    # transparent purple used to show the area
    COLOR = (170, 75, 255, 75)

    def __init__(self, position, owner, start_time, end_time=None):
        # center position of the area
        self.position = pygame.Vector2(position)
        # player number that threw the potion
        self.owner = owner
        # replay time when the potion broke
        self.start_time = start_time
        # stop at two seconds or at the replay cutoff
        self.end_time = min(
            start_time + self.DURATION,
            end_time if end_time is not None else start_time + self.DURATION,
        )
        # current area state
        self.elapsed = 0.0
        self.alive = True

    # update area lifetime
    def set_time(self, current_time):
        self.elapsed = max(0.0, current_time - self.start_time)
        self.alive = current_time < self.end_time

    # check if player is inside the area
    def contains_player(self, player_obj):
        # use the smaller friendly player hitbox for collision
        player_hitbox = player_obj.get_hitbox()
        # find the point on the hitbox closest to the circle
        closest_x = max(
            player_hitbox.left,
            min(self.position.x, player_hitbox.right),
        )
        closest_y = max(
            player_hitbox.top,
            min(self.position.y, player_hitbox.bottom),
        )
        # touching counts when the closest point is inside the radius
        return self.position.distance_squared_to((closest_x, closest_y)) <= self.RADIUS ** 2

    # draw transparent damage area
    def draw(self, surface):
        if not self.alive:
            return

        # use a separate alpha surface to make the circle transparent
        diameter = self.RADIUS * 2
        area_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(
            area_surface,
            self.COLOR,
            (self.RADIUS, self.RADIUS),
            self.RADIUS,
        )
        surface.blit(
            area_surface,
            (
                round(self.position.x - self.RADIUS),
                round(self.position.y - self.RADIUS),
            ),
        )
